from scipy.io import wavfile
import numpy as np


class AbstractJumpDetector:
    def __init__(self, filepath):
        self.filepath = filepath
        self.sample_rate, self.channels = wavfile.read(filepath)
        self.signal = np.average(self.channels, axis=1)

    @classmethod
    def handle(cls, filepath):
        instance = cls(filepath)
        res = instance.extract_jumps()
        if isinstance(res, np.ndarray): res = res.tolist()
        res = [list(i) for i in res]
        assert all(map(lambda x: len(x) == 2, res))
        return res

    def extract_jumps(self):
        raise NotImplementedError('(·.·)')
