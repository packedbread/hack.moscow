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

JUMP_DETECTOR_CLASS = algorithms.FirstJumpDetector

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
            self.jumps = np.array(await self.loop.run_in_executor(self.pool, target))
            self.status = 'ready'

            logging.debug('Postprocessing jumps...')
            self.jumps = np.array(await self.loop.run_in_executor(self.pool, self.postprocess_jumps))
            self.jumps.sort()
        finally:
            logging.debug('Cleaning up...')
            path = os.path.dirname(files[0])
            shutil.rmtree(path, ignore_errors=True)

    def _partition_jumps(self, window_size):
        ivalue_pairs = []
        for i, jump in enumerate(self.jumps):
            ivalue_pairs.append([i, jump[0]])
            ivalue_pairs.append([i, jump[1]])
        max_value = np.max(self.jumps)
        min_value = np.min(self.jumps)
        counts = [set() for _ in range(int((max_value - min_value + window_size - 1) / window_size + 1))]
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
                    jumps_to_remove.update(random.choices(list(left_items), k=len(left_items) - limit))
        for jump in self.jumps:
            if abs(jump[0] - jump[1]) < 2.0:
                jumps_to_remove.add(jump)
        return self.jumps[[i for i in range(self.jumps.shape[0]) if i not in jumps_to_remove]]

    def next_jump(self, current_time):
        first = 0
        for i in range(len(self.jumps)):
            if self.jumps[i][0] > current_time:
                first = i
                break
        answ = 0
        while True:
            if abs(current_time - self.jumps[first][0]) > 2 and random.randint(0, 100) < 5:
                answ = first
                break
            first += 1
            first %= len(self.jumps)
        return self.jumps[answ]
