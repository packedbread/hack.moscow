from concurrent.futures import ProcessPoolExecutor
from storage import ClientStorage
from aiohttp import web, hdrs
import aiofiles
import tempfile
import asyncio
import logging
import shutil
import os

MAX_FILE_SIZE = 20 * 1024 * 1024
PROCESS_POOL_SIZE = 8
STATIC_PATH = '../client/dist'
TEMP_PATH = 'temp'

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
clients = ClientStorage
clients.loop = loop = asyncio.get_event_loop()
clients.pool = pool = ProcessPoolExecutor(PROCESS_POOL_SIZE)
app = web.Application()
routes = web.RouteTableDef()


# Index page
@routes.get('/')
async def index(_):
    return web.FileResponse(STATIC_PATH + '/index.html')


# Upload multiple files
@routes.post('/upload')
@routes.route('OPTIONS', '/upload')
async def upload(request: web.Request):
    if request.method == 'OPTIONS':
        return web.Response(status=200)

    reader = await request.multipart()
    tempdir = tempfile.mkdtemp(dir=TEMP_PATH)
    files = []

    while True:
        field = await reader.next()
        if field is None: break
        if field.name != 'files[]': continue

        size = 0
        path = os.path.join(tempdir, str(len(files)))
        file = await aiofiles.open(path, mode='wb')

        while True:
            if size > MAX_FILE_SIZE:
                os.rmdir(tempdir)
                raise web.Response(status=403, text='Too large file')
            chunk = await field.read_chunk()
            if not chunk: break
            size += len(chunk)
            await file.write(chunk)

        await file.flush()
        await file.close()
        files.append(path)

    if not files: return web.Response(status=400, text='No files')

    client = ClientStorage()
    future = client.handle_upload(files)
    asyncio.ensure_future(future, loop=loop)
    logging.debug('New client storage: ' + client.uid)
    return web.Response(status=200, text=client.uid)


@routes.post('/next')
async def get_next(request):
    print(clients.clients)
    try: data = await request.json()
    except: data = {'time': 0}
    if not clients.clients: return web.HTTPNotFound()

    # Could get client by uid
    client = next(iter(clients.clients.values()))
    result = {
        'status': client.status,
        'ready': client.status == 'ready',
    }

    if client.status == 'ready':
        from_, to = client.next_jump(data['time'])
        result['from'], result['to'] = from_, to

    return web.json_response(data=result)


# Disable CORS globally
@app.on_response_prepare.append
async def on_prepare(_, response):
    response.headers[hdrs.ACCESS_CONTROL_ALLOW_ORIGIN] = '*'
    response.headers[hdrs.ACCESS_CONTROL_ALLOW_METHODS] = 'OPTIONS, GET, POST'
    response.headers[hdrs.ACCESS_CONTROL_ALLOW_HEADERS] = (
        'Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With'
    )


if __name__ == '__main__':
    # Cleanup temp dir
    shutil.rmtree(TEMP_PATH, ignore_errors=True)
    os.mkdir(TEMP_PATH)
    # Serve static & register routes
    routes.static('/', STATIC_PATH)
    app.add_routes(routes)
    # Start
    port = os.getenv('PORT', 5000)
    web.run_app(app, port=port)
