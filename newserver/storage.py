from functools import partial
from uuid import uuid4
import subprocess
import logging
import shutil
import os
import random
import numpy as np
from itertools import chain

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
            target = partial(self.merge, files)
            merged = await self.loop.run_in_executor(self.pool, target)
            if merged is None:
                logging.error('Merge failed')
                return

            logging.debug('Extracting jumps...')
            target = partial(JUMP_DETECTOR_CLASS.handle, merged)
            self.jumps = await self.loop.run_in_executor(self.pool, target)

            logging.debug('Postprocessing jumps...')
            self.jumps = await self.loop.run_in_executor(self.pool, self.postprocess_jumps)
        finally:
            logging.debug('Cleaning up...')
            path = os.path.dirname(files[0])
            shutil.rmtree(path, ignore_errors=True)

    def _partition_jumps(self, window_size):
        ivalue_pairs = []
        for i, jump in self.jumps:
            ivalue_pairs.append([i, jump[0]])
            ivalue_pairs.append([i, jump[1]])
        max_value = np.max(self.jumps)
        min_value = np.min(self.jumps)
        counts = [set()] * ((max_value - min_value + window_size - 1) / window_size)
        for index, value in ivalue_pairs:
            pos = int((value - min_value) / window_size)
            counts[pos].add(index)
        return counts

    def _jumps_percentile(self, q):
        return list(sorted(self.jumps, key=lambda jump: abs(jump[1] - jump[0])))[int(len(self.jumps) * q)]

    def postprocess_jumps(self):
        cascade_sizes = [1, 3, 10]
        cascade_limits = [5, 4, 5]
        jumps_to_remove = set()
        for size, limit in zip(cascade_sizes, cascade_limits):
            partition = self._partition_jumps(size)
            for items in partition:
                left_items = items.difference(jumps_to_remove)
                if len(left_items) > limit:
                    jumps_to_remove.update(random.choices(left_items, k=len(left_items) - limit))
        return self.jumps[[i for i in range(self.jumps.shape[0]) if i not in jumps_to_remove]]

    def make_next_jump(self, current_time):
        return random.choice(self.jumps)
