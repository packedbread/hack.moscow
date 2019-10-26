from aiohttp import web, hdrs
from scipy.io import wavfile
from tqdm import tqdm
from functools import partial
import logging
import os
import numpy as np
import tempfile
import asyncio
import ffmpeg
import time
import random
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


logger = logging.getLogger(__name__)


class PrecalcAlgo:
    def __init__(self, sample_rate, data):
        self.sample_rate = int(sample_rate)
        self.data = np.array(data)
        self.data = np.array([self.data[:, i] / np.max(np.abs(self.data[:, i])) for i in range(self.data.shape[1])]).T

    @staticmethod
    def _mse(a, b):
        return np.sqrt(np.sum(np.power(a - b, 2)))

    def _positional_value(self, window_size, first_start, second_start):
        first = self.data[first_start:first_start + window_size]
        second = self.data[second_start:second_start + window_size]
        first_padded = np.zeros((window_size,) + self.data.shape[1:])
        first_padded[:first.shape[0]] = first
        second_padded = np.zeros((window_size,) + self.data.shape[1:])
        second_padded[:second.shape[0]] = second
        return self._mse(first_padded, second_padded)

    def run(self):
        window_size = 2 * self.sample_rate
        stride = self.sample_rate
        threshold = 200
        result = []
        with ThreadPoolExecutor(16) as pool:
            def iteration(self, first_start):
                # print(f'Starting iteration {first_start // stride} at {time.time()}', flush=True)
                # start_time = time.time()
                is_accepted = np.array([
                    self._positional_value(window_size, first_start, second_start) < threshold
                    for second_start in range(first_start + stride, self.data.shape[0], stride)
                ])
                part = [(first_start, first_start + index * stride) for index, value in enumerate(is_accepted) if value]
                # end_time = time.time()
                # print(f'Finishing iteration {first_start // stride}, done in {int((end_time - start_time) * 1000)}ms', flush=True)
                return part

            for result_part in pool.map(partial(iteration, self), range(self.data.shape[0] // 8, self.data.shape[0], 4 * stride)):
                result.extend(result_part)
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
        algo = PrecalcAlgo(sample_rate, data)
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
        viable_options = self.result[[True if first > current_time or second > current_time else False for first, second in self.result]]
        if viable_options.size == 0:
            return random.choice(self.result)  # that is questionable

        def distance(option):
            return abs(option[0] - current_time) + abs(option[1] - current_time)

        distances = np.array([distance(option) for option in viable_options], dtype=np.float)
        return viable_options[self.roulette_selector(distances)]


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
