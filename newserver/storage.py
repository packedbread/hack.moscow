from functools import partial
from uuid import uuid4
import subprocess
import asyncio
import logging
import os
import random

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
        self.jumps = [[0, 1]]

    @staticmethod
    def transcode(filepath):
        logging.debug('Transcoding: %s', filepath)
        cmd = f'ffmpeg -i {filepath} -acodec pcm_s16le -ar 44100 {filepath + ".wav"}'
        code = subprocess.call(cmd.split())
        if code != 0:
            logging.error('Transcode error (code %s)', code)
            return None
        logging.debug('Transcoding done: %s', filepath + '.wav')
        return filepath + '.wav'

    @staticmethod
    def merge(files):
        path = os.path.dirname(files[0])
        output = os.path.join(path, 'joined.wav')
        items = '|'.join(files)
        cmd = f'ffmpeg -i concat:{items} -acodec pcm_s16le -ar 44100 {output}'
        code = subprocess.call(cmd.split())
        if code != 0:
            logging.error('Merge error (code %s)', code)
            return None
        return output

    async def handle_upload(self, files):
        # converted = filter(None, self.pool.map(self.transcode, files))

        res = await self.loop.run_in_executor(self.pool, partial(self.merge, files))
        print(res)

        # tasks = [self.loop.run_in_executor(self.pool, self.transcode, file) for file in files]
        # await asyncio.wait(*tasks, loop=self.loop)
        # print(tasks, tasks[0].result)

        #######################################
        # Here you have filepaths of ready wavs
        #######################################

        return 123

    def make_next_jump(self, current_time):
        return random.choice(self.jumps)
