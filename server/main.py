from aiohttp import web, hdrs
from scipy.io import wavfile
from scipy.fftpack import rfft
from functools import partial
import logging
import os
import numpy as np
import tempfile
import asyncio
import ffmpeg
import time
from skimage import util
import random
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


logger = logging.getLogger(__name__)


def polynomial_hash(arr, p):
    base = 1
    ans = 0
    for i in range(len(arr)):
        ans += i * base
        base *= p
    return ans


class PrecalcMediumFFTAlgo:
    def __init__(self, sample_rate, data):
        self.sample_rate = int(sample_rate)
        data = np.array(data)
        data = np.array([data[:, i] / np.max(np.abs(data[:, i])) for i in range(data.shape[1])]).T
        self.one_channel = np.average(data, axis=1)

    @staticmethod
    def _mse(a, b):
        return np.sqrt(np.sum(np.power(a - b, 2)))

    def _get_fft_hash(self, from_sample, window_size):
        freq_arr = rfft(self.one_channel[from_sample: from_sample + window_size])
        windowed = util.view_as_blocks(freq_arr, (100, ))
        block_sum = np.array(list(map(np.sum, windowed)))

        arr_hash = polynomial_hash(block_sum, 113)
        arr_hash /= 1000
        arr_hash = round(arr_hash, 4)

        return [arr_hash, from_sample]

    # def _positional_value(self, window_size, first_start, second_start):
    #     first = self.data[first_start:first_start + window_size]
    #     second = self.data[second_start:second_start + window_size]
    #     first_padded = np.zeros((window_size,) + self.data.shape[1:])
    #     first_padded[:first.shape[0]] = first
    #     second_padded = np.zeros((window_size,) + self.data.shape[1:])
    #     second_padded[:second.shape[0]] = second
    #     return self._mse(first_padded, second_padded)

    def run(self):
        start_time = time.time()
        window_size = 1000
        stride = 64
        hash_result = defaultdict(lambda: [])
        result = []
        with ThreadPoolExecutor(16) as pool:
            def iteration(first_start):
                hsh = self._get_fft_hash(first_start, window_size)
                return hsh, first_start

            def map_append(index_list):
                res = []
                for i in range(len(index_list)):
                    for j in range(i + 1, len(index_list)):
                        if abs(index_list[j] - index_list[i]) > np.float(self.sample_rate) * 2:
                            res.append([index_list[i], index_list[j]])
                return res

            for result_part in pool.map(
                iteration, range(
                    len(self.one_channel) // 10,
                    len(self.one_channel) - window_size - len(self.one_channel) // 10, stride
                )
            ):
                hash_result[result_part[0][0]].append(result_part[0][1])

            for result_part in pool.map(map_append, (item for _, item in hash_result.items())):
                result.extend(result_part)

        end_time = time.time()
        print(f'Finished PrecalcMediumFFTAlgo precalc, done in {int((end_time - start_time) * 1000)}ms.', flush=True)
        logger.error(result)

        return np.array(result, dtype=np.float) / np.float(self.sample_rate)


class NonCommonMaxFrequenceIndexesAlgo:
    def __init__(self, sample_rate, data):
        self.sample_rate = sample_rate
        self.signal = np.average(data, axis=1)
        self.signal /= np.max(np.abs(self.signal))

    def run(self, window_size=4096, stride=256, n=6, threshold=None):
        print('Starting NonCommonMaxFrequenceIndexesAlgo precalc...', flush=True)
        start_time = time.time()
        threshold = threshold or 7 * n // 8
        windows = util.view_as_windows(self.signal, window_shape=(window_size,), step=stride)
        windows = windows * np.hanning(window_size)

        print('Beginning window fft...', flush=True)
        spectrum = np.abs(np.fft.fft(windows, axis=0))[:window_size // 2]
        frequencies = np.fft.fftfreq(window_size)[:window_size // 2] * self.sample_rate
        print('Finished window fft.', flush=True)

        def lowest_index(window, lowest_frequency=30):
            return next(i for i, value in enumerate(frequencies) if value > lowest_frequency)

        def highest_index(window, highest_frequency=400):
            return next(len(frequencies) - i for i, value in enumerate(reversed(frequencies)) if value < highest_frequency)

        def poly_hash(data, P=79):
            value = 0
            power = 1
            for v in data:
                value += v * power
                power *= P
            return value

        index_hex = np.array([np.argmax(window[lowest_index(window):highest_index(window)]) for window in spectrum])
        counter = Counter(index_hex)
        print(f'Counter 3 most common frequencies: {counter.most_common(3)}', flush=True)
        most_common_index = counter.most_common(1)[0][0]

        ngram_dict = defaultdict(list)
        current_ngram = [0] + index_hex[:n]
        for i, index in enumerate(index_hex[n:], n):
            current_ngram = list(current_ngram[1:]) + [index]
            if current_ngram.count(most_common_index) >= threshold:
                continue
            ngram_dict[poly_hash(current_ngram)].append(i - n + 1)

        print('All viable edge transfers: ', flush=True)
        for key, value in ngram_dict.items():
            if len(value) > 1:
                print(key, value)

        edges = []
        for key, value in ngram_dict.items():
            for index, first in enumerate(value):
                for second in value[index + 1:]:
                    edges.append([first, second])
        end_time = time.time()
        print(f'Finished NonCommonMaxFrequenceIndexesAlgo precalc, done in {int(end_time - start_time) * 1000}ms.', flush=True)
        return np.array(edges, dtype=np.float) / self.sample_rate


process_pool_executor = ProcessPoolExecutor(1)
loop = asyncio.get_event_loop()
song_edges = None


class TaskResultStorage:
    def __init__(self):
        self.result = None

    @property
    def is_ready(self):
        return self.result is not None


task_result_storage = TaskResultStorage()


async def spawn_task(content):
    file = tempfile.NamedTemporaryFile()
    file.write(content)
    task = FileProcessingTask(file.name)
    payload = partial(task.do_payload, task.generate_unique_task_id(), task.filename)
    task_result_storage.result = await loop.run_in_executor(process_pool_executor, payload)
    file.close()


class FileProcessingTask:
    def __init__(self, filename):
        global task_result_storage
        task_result_storage = TaskResultStorage()
        self.filename = filename

    @staticmethod
    def generate_unique_task_id():
        return 'default'

    @staticmethod
    def do_payload(unique_task_id, filename):
        wav_filename = f'{unique_task_id}.wav'
        # convert file to .wav
        ffmpeg.input(filename).output(wav_filename).overwrite_output().run()
        # load .wav
        sample_rate, data = wavfile.read(wav_filename)
        # precalculation
        algo = PrecalcMediumFFTAlgo(sample_rate, data)
        # return results
        print('Starting main precalc...')
        start_time = time.time()
        result = algo.run()
        end_time = time.time()
        print(f'Finished main precalc, done in {int((end_time - start_time) * 1000)}ms.')
        return result


class NextJumpAlgo:
    def __init__(self, result):
        self.result = result

    def roulette_selector(self, values):
        values = np.array(values, dtype=np.float)
        values /= np.sum(values)
        cummulative = [0]
        for dist_perc in values:
            cummulative.append(dist_perc + cummulative[-1])
        value = random.random()

        def bin_find(value):
            left = 0
            right = len(cummulative) - 1
            while right - left > 1:
                middle = left + (right - left) // 2
                if cummulative[middle] > value:
                    right = middle
                else:
                    left = middle
            return left

        return bin_find(value)

    def get_next_jump(self, current_time):
        # viable_options = self.result[[True if first > current_time or second > current_time else False for first, second in self.result]]
        # if viable_options.size == 0:
        return random.choice(self.result)  # that is questionable

        # def distance(option):
        #     return abs(option[0] - current_time) + abs(option[1] - current_time)
        #
        # distances = np.array([distance(option) for option in viable_options], dtype=np.float)
        # return viable_options[self.roulette_selector(distances)]


routes = web.RouteTableDef()


DEFAULT_TEXT = '''
####### ####### ####### ######     #     #  #####  ### 
#       #       #       #     #    #     # #     # ### 
#       #       #       #     #    #     # #       ### 
#####   #####   #####   #     #    #     #  #####   #  
#       #       #       #     #    #     #       #     
#       #       #       #     #    #     # #     # ### 
#       ####### ####### ######      #####   #####  ###
'''


@routes.get('/')
async def index(_):
    return web.Response(text=DEFAULT_TEXT)


@routes.post('/upload')
async def upload(request):
    print('Started file upload...', flush=True)
    start_time = time.time()
    content = await request.content.read()
    end_time = time.time()
    print(f'Finished file upload, done in {int((end_time - start_time) * 1000)}ms.', flush=True)

    asyncio.ensure_future(spawn_task(content), loop=loop)
    return web.Response(status=200)


@routes.route('OPTIONS', '/upload')
async def upload_options(_):
    return web.Response(status=200)


@routes.post('/next')
async def get_next(request):
    current_time = (await request.json())['current_time']
    if task_result_storage.is_ready:
        algo = NextJumpAlgo(task_result_storage.result)
        next_jump = algo.get_next_jump(current_time)
        print(next_jump)
        return web.json_response(data={'from': next_jump[0], 'to': next_jump[1]})
    else:
        return web.Response(status=422)


app = web.Application()
app.add_routes(routes)
logging.basicConfig(level=logging.DEBUG)


async def on_prepare(_, response):
    response.headers[hdrs.ACCESS_CONTROL_ALLOW_ORIGIN] = '*'
    response.headers[hdrs.ACCESS_CONTROL_ALLOW_METHODS] = 'OPTIONS, GET, POST'
    response.headers[hdrs.ACCESS_CONTROL_ALLOW_HEADERS] = 'Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With'

app.on_response_prepare.append(on_prepare)


if __name__ == '__main__':
    web.run_app(app, port=os.getenv('PORT', 5000))
