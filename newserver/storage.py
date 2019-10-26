from functools import partial
from uuid import uuid4
import subprocess
import logging
import shutil
import os
import random

import algorithms

JUMP_DETECTOR_CLASS = algorithms.SecondJumpDetector

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
        self.status = 'idling'
        self.jumps = None

    @staticmethod
    def transcode(filepath):
        cmd = f'ffmpeg -i {filepath} -acodec pcm_s16le -ar 44100 {filepath + ".wav"}'
        code = subprocess.call(cmd.split())
        if code != 0: return None
        return filepath + '.wav'

    @staticmethod
    def merge(files):
        path = os.path.dirname(files[0])
        output = os.path.join(path, 'joined.wav')
        items = '|'.join(files)
        cmd = f'ffmpeg -i concat:{items} -acodec pcm_s16le -ar 44100 {output}'
        code = subprocess.call(cmd.split())
        if code != 0: return None
        return output

    async def handle_upload(self, files):
        try:
            logging.debug('Merging files...')
            self.status = 'merging'
            target = partial(self.merge, files)
            merged = await self.loop.run_in_executor(self.pool, target)
            if merged is None:
                logging.error('Merge failed')
                return

            logging.debug('Extracting jumps...')
            self.status = 'extracting'
            target = partial(JUMP_DETECTOR_CLASS.handle, merged)
            self.jumps = await self.loop.run_in_executor(self.pool, target)
            self.status = 'ready'
        finally:
            logging.debug('Cleaning up...')
            path = os.path.dirname(files[0])
            shutil.rmtree(path, ignore_errors=True)

    def next_jump(self, current_time):
        # TODO
        return random.choice(self.jumps)
