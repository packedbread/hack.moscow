from uuid import uuid4
import logging
import ffmpeg

logger = logging.getLogger(__name__)


class ClientStorage:
    """
    Hold client-related stuff here (jump states, seeds, etc.)
    """

    pool = None
    loop = None
    clients = {}

    def __init__(self):
        self.uid = str(uuid4())
        self.clients[self.uid] = self

    @staticmethod
    def transcode(filepath):
        logging.debug('Transcoding: %s', filepath)
        try:
            ffmpeg.input(filepath).output(filepath + '.wav').run()
        except Exception as err:
            logging.error('FFMpeg transcode failed: %s', err)
            return None
        logging.debug('Transcoding done: %s', filepath + '.wav')
        return filepath + '.wav'

    async def handle_upload(self, files):
        res = self.pool.map(self.transcode, files)
        print(res)
        # tasks = [self.loop.run_in_executor(self.pool, self.transcode, file) for file in files]
        # await asyncio.wait(*tasks, loop=self.loop)
        # print(tasks, tasks[0].result)

        #######################################
        # Here you have filepaths of ready wavs
        #######################################

        return 123
