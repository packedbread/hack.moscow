from concurrent.futures import ThreadPoolExecutor
from .abstract import AbstractJumpDetector
from collections import defaultdict
from scipy.fftpack import rfft
from skimage import util
import numpy as np
import logging
import time

logger = logging.getLogger(__name__)


class FirstJumpDetector(AbstractJumpDetector):
    def __init__(self, path):
        super().__init__(path)
        self.one_channel = self.signal

    def extract_jumps(self):
        return self.run()

    @staticmethod
    def _mse(a, b):
        return np.sqrt(np.sum(np.power(a - b, 2)))

    @staticmethod
    def calc_hash(arr):
        ans = 0
        for i in range(len(arr)):
            ans += arr[i]

        return ans

    def _get_fft_hash(self, from_sample, window_size):
        freq_arr = rfft(self.one_channel[from_sample: from_sample + window_size])
        windowed = util.view_as_blocks(freq_arr, (40,))
        block_sum = np.array(list(map(np.sum, windowed)))

        arr_hash = self.calc_hash(block_sum)
        arr_hash = round(arr_hash, 4)

        return [arr_hash, from_sample + window_size / 2]

    def run(self):
        start_time = time.time()
        window_size = 44000
        stride = 1000
        hash_result = []
        result = []
        with ThreadPoolExecutor(16) as pool:
            def iteration(first_start):
                hsh = self._get_fft_hash(first_start, window_size)
                return hsh, first_start

            # def map_append(index_list):
            #     res = []
            #     for i in range(len(index_list)):
            #         for j in range(i + 1, len(index_list)):
            #             if abs(index_list[j] - index_list[i]) > np.float(self.sample_rate) * 2:
            #                 res.append([index_list[i], index_list[j]])
            #     return res

            for result_part in pool.map(
                    iteration, range(
                        len(self.one_channel) // 10,
                        len(self.one_channel) - window_size - len(self.one_channel) // 10, stride
                    )
            ):
                hash_result.append(result_part[0])

        hash_result.sort()
        max_hash = hash_result[-1][0]
        for i in range(len(hash_result) - 1):
            if hash_result[i + 1][0] - hash_result[i][0] < max_hash / 1000000:
                result.append([hash_result[i][1], hash_result[i + 1][1]])

        end_time = time.time()
        print(f'Finished PrecalcMediumFFTAlgo precalc, done in {int((end_time - start_time) * 1000)}ms.', flush=True)
        logger.critical(hash_result)
        logger.critical(len(result))
        print(hash_result, flush=True)
        print(len(result), flush=True)

        return np.array(result, dtype=np.float) / np.float(self.sample_rate)
