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

    def _get_fft_hash(self, from_sample, window_size):
        freq_arr = rfft(self.one_channel[from_sample: from_sample + window_size])
        windowed = util.view_as_blocks(freq_arr, (100,))
        arr_hash = 10 * np.max(windowed) + np.sum(windowed)
        arr_hash /= 1000
        arr_hash = round(arr_hash, 4)

        return [arr_hash, from_sample]

    # def _positional_value(self, window_size, first_start, second_start):
    #     first = self.data[first_start:first_start + window_size]
    #     second = self.data[second_start:second_start + window_size]
    #     first_padded = np.zeros((window_size,) + self.data.shape[1:])
    #     first_padded[:first.shape[0]] = first
    #     second_padded = np.zeros((window_size,) + self.data.shape[1:])
    #     second_padded[:second.shape[0]] = second
    #     return self._mse(first_padded, second_padded)

    def run(self):
        start_time = time.time()
        window_size = 1000
        stride = 64
        hash_result = defaultdict(lambda: [])
        result = []
        with ThreadPoolExecutor(16) as pool:
            def iteration(first_start):
                hsh = self._get_fft_hash(first_start, window_size)
                return hsh, first_start

            def map_append(index_list):
                res = []
                for i in range(len(index_list)):
                    for j in range(i + 1, len(index_list)):
                        if abs(index_list[j] - index_list[i]) > np.float(self.sample_rate) * 2:
                            res.append([index_list[i], index_list[j]])
                return res

            for result_part in pool.map(
                    iteration, range(
                        len(self.one_channel) // 10,
                        len(self.one_channel) - window_size - len(self.one_channel) // 10, stride
                    )
            ):
                hash_result[result_part[0][0]].append(result_part[0][1])

            for result_part in pool.map(map_append, (item for _, item in hash_result.items())):
                result.extend(result_part)

        end_time = time.time()
        print(f'Finished PrecalcMediumFFTAlgo precalc, done in {int((end_time - start_time) * 1000)}ms.', flush=True)
        logger.error(result)

        return np.array(result, dtype=np.float) / np.float(self.sample_rate)
