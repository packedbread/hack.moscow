from collections import Counter, defaultdict
from scipy.fftpack import rfft
from .abstract import AbstractJumpDetector
from skimage import util
import numpy as np
import logging
import time

logger = logging.getLogger(__name__)


class NonCommonMaxFrequenceIndexesAlgoJumpDetector(AbstractJumpDetector):
    def extract_jumps(self):
        return self.run()

    def run(self, window_size=4096, stride=256, n=8, threshold=None):
        print('Starting NonCommonMaxFrequenceIndexesAlgo precalc...', flush=True)
        start_time = time.time()
        threshold = threshold or 6 * n // 8
        windows = util.view_as_windows(self.signal, window_shape=(window_size,), step=stride)
        windows = windows * np.hanning(window_size)

        print('Beginning window fft...', flush=True)
        spectrum = rfft(windows)

        frequencies = np.fft.fftfreq(window_size)[:window_size // 2] * self.sample_rate
        print('Finished window fft.', flush=True)

        def lowest_index(window, lowest_frequency=30):
            return next(i for i, value in enumerate(frequencies) if value > lowest_frequency)

        def highest_index(window, highest_frequency=400):
            return next(len(frequencies) - i for i, value in enumerate(reversed(frequencies)) if value < highest_frequency)

        def poly_hash(data, P=79):
            value = 0
            power = 1
            for v in data:
                value += v * power
                power *= P
            return value

        index_hex = np.array([np.argmax(window[lowest_index(window):highest_index(window)]) for window in spectrum])
        counter = Counter(index_hex)
        print(f'Counter 3 most common frequencies: {counter.most_common(3)}', flush=True)
        most_common_index = counter.most_common(1)[0][0]

        ngram_dict = defaultdict(list)
        current_ngram = [0] + index_hex[:n]
        for i, index in enumerate(index_hex[n:], n):
            current_ngram = list(current_ngram[1:]) + [index]
            if current_ngram.count(most_common_index) >= threshold:
                continue
            ngram_dict[poly_hash(current_ngram)].append(i * stride + window_size / 2)

        print('All viable edge transfers: ', flush=True)
        for key, value in ngram_dict.items():
            if len(value) > 1:
                print(key, np.array(value) / self.sample_rate)

        edges = []
        for key, value in ngram_dict.items():
            for index, first in enumerate(value):
                for second in value[index + 1:]:
                    edges.append([first, second])
        end_time = time.time()
        print(f'Finished NonCommonMaxFrequenceIndexesAlgo precalc, done in {int(end_time - start_time) * 1000}ms.', flush=True)
        return np.array(edges, dtype=np.float) / self.sample_rate
