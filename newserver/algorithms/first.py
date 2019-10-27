from concurrent.futures import ThreadPoolExecutor
from .abstract import AbstractJumpDetector
from collections import defaultdict
from scipy.fftpack import rfft
from tqdm import tqdm
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
            ans += arr[i] * (len(arr) - i) / len(arr)

        return ans

    def _get_fft_hash(self, from_sample, window_size):
        freq_arr = rfft(self.one_channel[from_sample: from_sample + window_size])
        x = np.argmax(freq_arr)
        return x

    def run(self):
        start_time_os = time.time()
        window_size = 22000
        stride = 500
        result = []

        start_time = len(self.one_channel) // 100
        end_time = len(self.one_channel) - window_size - len(self.one_channel) // 100

        hash_result = [0] * ((int(end_time) - int(start_time) + stride - 1) // int(stride))

        with ThreadPoolExecutor(16) as pool:
            def iteration(first_start):
                hsh = self._get_fft_hash(first_start, window_size)
                return hsh, first_start

            for result_part in pool.map(iteration, range(start_time, end_time, stride)):
                hash_result[(result_part[1] - start_time) // stride] = result_part[0]


        hash_map = defaultdict(lambda: [])
        chunk_length = 30
        temp, mod = int(0), int(117)
        MOD = int(1e9 + 7)
        kek = int(mod**(chunk_length - 1)) % MOD


        for i in range(chunk_length):
            temp *= mod
            temp %= MOD
            temp = int(temp + hash_result[i])
            temp %= MOD

        hash_map[temp] = [0]

        for i in range(1, len(hash_result) - chunk_length + 1):
            temp -= kek * int(hash_result[i - 1])
            temp = (temp + MOD) % MOD
            temp *= mod
            temp %= MOD
            temp += hash_result[i + chunk_length - 1]
            temp %= MOD

            hash_map[temp].append(start_time + i * stride)

        for _, item in tqdm(hash_map.items()):
            for i in range(len(item)):
                for j in range(i + 1, len(item)):
                    result.append([item[i], item[j]])

        end_time_os = time.time()
        print(f'Finished PrecalcMediumFFTAlgo precalc, done in {int((end_time_os - start_time_os) * 1000)}ms.', flush=True)
        print(len(result), flush=True)

        return np.array(result, dtype=np.float) / np.float(self.sample_rate)
