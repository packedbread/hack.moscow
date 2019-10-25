from aiohttp import web
import logging

logger = logging.getLogger(__name__)


def leo_algo(sss):
    pass


def leo_answer(t_from, t_to):
    return b'aaa'


async def upload_handler(request):
    content = await request.content.read()
    leo_algo(content)
    return web.Response(status=200)


async def response_handler(request):
    time_from = request.match_info.get("from")
    time_to = request.match_info.get("to")
    response_byte_arr = leo_answer(time_from, time_to)

    return web.Response(body=response_byte_arr)


app = web.Application()
app.add_routes([web.post('/upload', upload_handler),
                web.get(r'/from{from}to{to}', response_handler)])

if __name__ == '__main__':
    web.run_app(app)
