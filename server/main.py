from aiohttp import web, hdrs
from scipy.io import wavfile
from tqdm import tqdm
from functools import partial
import logging
import os
import io
import numpy as np
import random
import tempfile
import asyncio
from concurrent.futures import ProcessPoolExecutor


logger = logging.getLogger(__name__)


class Algorithm:
    def __init__(self, sample_rate, data):
        self.sample_rate = int(sample_rate)
        self.data = np.array([data[:, i] / np.max(np.abs(data[:, i])) for i in range(data.shape[1])]).T

    def _mse(self, a, b):
        return np.sum(np.power(a - b, 2))

    def _positional_value(self, window_size, first_start, second_start):
        first = self.data[first_start:first_start + window_size]
        second = self.data[second_start:second_start + window_size]
        first_padded = np.zeros((window_size,) + self.data.shape[1:])
        first_padded[:first.shape[0]] = first
        second_padded = np.zeros((window_size,) + self.data.shape[1:])
        second_padded[:second.shape[0]] = second
        return self._mse(first_padded, second_padded)

    def edges(self, window_size=None, stride=None, threshold=1453.8958203047514):
        window_size = window_size or 2 * self.sample_rate
        stride = stride or self.sample_rate
        result = []
        for first_start in tqdm(range(0, self.data.shape[0], stride)):
            is_accepted = np.array([
                self._positional_value(window_size, first_start, second_start) < threshold
                for second_start in range(first_start + stride, self.data.shape[0], stride)
            ])
            result.extend([(first_start, first_start + index * stride) for index, value in enumerate(is_accepted) if value])
        return np.array(result, dtype=np.float) / np.float(self.sample_rate)


def process_new_input(filename):
    algorithm = Algorithm(*wavfile.read(filename))
    return algorithm.edges()


executor = ProcessPoolExecutor(1)
loop = asyncio.get_event_loop()
song_edges = None


async def spawn_job(content):
    global song_edges
    print('kok', flush=True)
    file = tempfile.NamedTemporaryFile()
    file.write(content)
    result = await loop.run_in_executor(executor, process_new_input, file.name)
    file.close()
    song_edges = result


async def upload_handler(request):
    print('Received file', flush=True)
    content = await request.content.read()
    print('Loaded file', flush=True)
    asyncio.ensure_future(spawn_job(content), loop=loop)
    return web.Response(status=200)


async def edges_handler(request):
    if song_edges is None:
        return web.Response(status=422)
    return web.json_response(data=song_edges.tolist())


async def main_page_handler(request):
    return web.Response(status=200, content_type='application/text')


async def audio(_):
    return web.FileResponse('./tron.wav')


async def on_prepare(_, response):
    response.headers[hdrs.ACCESS_CONTROL_ALLOW_ORIGIN] = '*'
    response.headers[hdrs.ACCESS_CONTROL_ALLOW_METHODS] = 'OPTIONS,GET,POST'


app = web.Application()
logging.basicConfig(level=logging.DEBUG)
app.on_response_prepare.append(on_prepare)
app.add_routes([
    web.get('/audio', audio),
    web.post('/upload', upload_handler),
    web.get('/edges', edges_handler),
    web.get('/', main_page_handler)
])

if __name__ == '__main__':
    web.run_app(app, port=os.getenv('PORT', 5000))
