from aiohttp import web, hdrs
from scipy.io import wavfile
from scipy.fftpack import rfft
from functools import partial
import logging
import os
import math
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
    base = 1.
    ans = 0.
    for i in range(len(arr)):
        ans += (arr[i] * arr[i])
    return math.sqrt(ans)


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

        # arr_hash = polynomial_hash(block_sum, 47)
        arr_hash = np.sum(block_sum)
        # arr_hash = arr_hash
        arr_hash = round(arr_hash, 4)

        return [arr_hash, from_sample + window_size / 2]

    def run(self):
        start_time = time.time()
        window_size = 2 * 44000
        stride = 500
        hash_result = []
        result = []
        with ThreadPoolExecutor(16) as pool:
            def iteration(first_start):
                hsh = self._get_fft_hash(first_start, window_size)
                return hsh, first_start

            # def map_append(index_list):
            #     res = []
            #     for i in range(len(index_list)):
            #         for j in range(i + 1, len(index_list)):
            #             if abs(index_list[j] - index_list[i]) > np.float(self.sample_rate) * 2:
            #                 res.append([index_list[i], index_list[j]])
            #     return res

            for result_part in pool.map(
                iteration, range(
                    len(self.one_channel) // 10,
                    len(self.one_channel) - window_size - len(self.one_channel) // 10, stride
                )
            ):
                hash_result.append(result_part[0])

        hash_result.sort()
        max_hash = hash_result[-1][0]
        for i in range(len(hash_result) - 1):
            if hash_result[i + 1][0] - hash_result[i][0] < max_hash / 100000:
                result.append([hash_result[i][1], hash_result[i + 1][1]])

        end_time = time.time()
        print(f'Finished PrecalcMediumFFTAlgo precalc, done in {int((end_time - start_time) * 1000)}ms.', flush=True)
        logger.error(hash_result)
        logger.error(len(result))

        return np.array(result, dtype=np.float) / np.float(self.sample_rate)


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
