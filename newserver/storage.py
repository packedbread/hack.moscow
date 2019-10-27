from functools import partial
from uuid import uuid4
import subprocess
import logging
import shutil
import os
import random
import numpy as np

import algorithms

BASE_FFMPEG_CMD = 'ffmpeg -hide_banner -loglevel quiet '
JUMP_DETECTOR_CLASS = algorithms.FirstJumpDetector

logger = logging.getLogger('Storage')


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
        self.composition_length = None

    @staticmethod
    def transcode(filepath):
        cmd = BASE_FFMPEG_CMD + f'-i {filepath} -acodec pcm_s16le -ar 44100 {filepath + ".wav"}'
        code = subprocess.call(cmd.split())
        if code != 0: return None
        return filepath + '.wav'

    @staticmethod
    def merge(files):
        path = os.path.dirname(files[0])
        output = os.path.join(path, 'joined.wav')
        items = '|'.join(files)
        cmd = BASE_FFMPEG_CMD + f'-i concat:{items} -acodec pcm_s16le -ar 44100 {output}'
        code = subprocess.call(cmd.split())
        if code != 0: return None
        return output

    async def handle_upload(self, files):
        try:
            logging.critical('Merging files...')
            self.status = 'merging'
            target = partial(self.merge, files)
            merged = await self.loop.run_in_executor(self.pool, target)
            if merged is None:
                logging.error('Merge failed')
                return

            logging.critical('Extracting jumps...')
            self.status = 'extracting'
            target = partial(JUMP_DETECTOR_CLASS.handle, merged)
            self.jumps, self.composition_length = await self.loop.run_in_executor(self.pool, target)
            self.jumps = np.array(self.jumps)
            self.status = 'ready'

            logging.critical('Postprocessing jumps...')
            self.jumps = np.array(await self.loop.run_in_executor(self.pool, self.postprocess_jumps))
            self.jumps.sort()
        except Exception as err:
            logging.critical('CRASHED', exc_info=err)
            self.status = 'crashed'
        finally:
            logging.critical('Cleaning up...')
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
        for i, jump in enumerate(self.jumps):
            if abs(jump[0] - jump[1]) < 2.0:
                jumps_to_remove.add(i)
        return self.jumps[[i for i in range(self.jumps.shape[0]) if i not in jumps_to_remove]]

    def _roulette_selector(self, values):
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

    def next_jump(self, current_time):
        def distance(jump):
            jump.sort()
            if jump[0] > current_time:
                return jump[0] - current_time
            elif jump[1] > current_time:
                return jump[1] - current_time
            else:
                return self.composition_length - current_time + jump[0]

        def length(jump):
            return abs(jump[0] - jump[1])

        distances = np.array([distance(jump) for jump in self.jumps], dtype=np.float)
        distances /= np.sum(distances)

        lengths = np.array([length(jump) for jump in self.jumps], dtype=np.float)
        lengths /= np.sum(lengths)

        distances_weight = -0.5

        normed_probs = distances * distances_weight + lengths * (1.0 - distances_weight)

        return self.jumps[self._roulette_selector(normed_probs)]
