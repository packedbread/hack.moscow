from aiohttp import web, hdrs
import wave
import logging
import os

logger = logging.getLogger(__name__)


def leo_algo(sss):
    pass


def leo_answer(t_from, t_to):
    wav = wave.open('tron.wav', 'rb')
    return wav.readframes(wav.getframerate() * 5)


async def upload_handler(request):
    content = await request.content.read()
    leo_algo(content)
    return web.Response(status=200)


async def response_handler(request):
    time_from = request.match_info.get("from")
    time_to = request.match_info.get("to")
    response_byte_arr = leo_answer(time_from, time_to)

    return web.Response(body=response_byte_arr)


async def main_page_handler(request):
    return web.Response(status=200)


async def audio(_):
    return web.FileResponse('./tron.wav')


async def on_prepare(_, response):
    response.headers[hdrs.ACCESS_CONTROL_ALLOW_ORIGIN] = '*'


app = web.Application()
app.on_response_prepare.append(on_prepare)
app.add_routes([
    web.get('/audio', audio),
    web.post('/upload', upload_handler),
    web.get('/from{from}to{to}', response_handler),
    web.get('/', main_page_handler)
])

web.run_app(app, port=os.getenv('PORT', 5000))
