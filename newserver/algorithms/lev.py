from .abstract import AbstractJumpDetector
from scipy.signal import butter, lfilter
import numpy as np


class LevJumpDetector(AbstractJumpDetector):
    def extract_jumps(self):
        return RUNLEVA(self.sample_rate, self.channels)


def RUNLEVA(sample_rate, channels):
    data_length = channels[:, 0].shape[0]
    data = (channels[:, 0] + channels[:, 1]) / 2  # todo: that's going to change
    amplitude = max(max(data), -min(data))
    data = list(map(lambda x: x / amplitude, data))

    left = sample_rate * 10
    right = sample_rate * 40

    TACTSIZE = 2
    LEVADEBIL = True

    def butter_lowpass(cutoff, fs, order=5):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        return b, a

    def butter_lowpass_filter(data, cutoff, fs, order=5):
        b, a = butter_lowpass(cutoff, fs, order=order)
        y = lfilter(b, a, data)
        return y

    def FILTERBLYAT(data, cutoff):
        # Filter requirements.
        order = 6

        # Filter the data, and plot both the original and filtered signals.
        y = butter_lowpass_filter(data, cutoff, sample_rate, order)
        return y

    def CountEnergy(musik, sample=1024):
        E = []
        curE = 0
        for i in range(sample):
            curE += musik[i] ** 2
        for i in range(0, len(musik) - sample):
            curE += musik[i + sample] ** 2
            curE -= musik[i] ** 2
            E.append(curE)
        return E

    def MAXWINDOW(arr, sample, threshold):
        stack = []
        res = []
        for i in range(0, sample):
            while len(stack) > 0 and arr[stack[-1]] < arr[i + sample]:
                stack.pop()
            stack.append(i)
        for i in range(0, len(arr) - sample):
            while len(stack) > 0 and arr[stack[-1]] < arr[i + sample]:
                stack.pop()
            stack.append(i + sample)
            value = stack[0]
            if arr[value] < threshold:
                value = 0
            res.append(arr[value])
            if stack[0] == i:
                stack.pop(0)
        return res

    def FINDPEAKS(arr, step, thres):
        i = 0
        peaks = []
        while (i < len(arr)):
            if arr[i] > thres:
                peaks.append(i)
                i += step
            i += 1
        return peaks

    def CNTBPM(peaks):
        bpms = []
        for i in range(60, 180):
            bpms.append(60 * sample_rate / i)

        cnt = dict()
        for i in range(len(bpms)):
            cnt[bpms[i]] = 0

        for i in range(len(peaks) - 1):
            a = peaks[i]
            b = peaks[i + 1]
            val = (b - a)
            while val > bpms[0]:
                val /= 2
            while val < bpms[-1]:
                val *= 2
            cbpm = 0
            for j in range(len(bpms)):
                if abs(bpms[cbpm] - val) > abs(bpms[j] - val):
                    cbpm = j

            cnt[bpms[cbpm]] += 1

        srt = []
        for k, v in cnt.items():
            srt.append([v, k])

        srt.sort(reverse=True)
        avg = 0
        cnt = 0
        for i in range(len(srt)):
            if srt[i][0] == srt[0][0]:
                avg += srt[i][1]
                cnt += 1
        return round(60 * sample_rate / (avg / cnt))

    def GETTACTS(data, pkst, bpm, slid = 0):
        tacts = []
        smpl = 60 * sample_rate // bpm
        start = pkst
        pkst -= slid * smpl
        while start > 0:
            start -= smpl * 4
        start += smpl * 4
        for i in range(start, len(data), smpl):
            tacts.append(data[i:(i+smpl)])
        return tacts, start, smpl

    def GETTACTSIND(data, start, bpm):
        tacts = []
        smpl = 60 * sample_rate // bpm
        for i in range(start, len(data), smpl):
            tacts.append(i)
        return tacts

    def GETPEAKSTART(peaks, bpm, peaksneeded):
        smpl = 60 * sample_rate // bpm
        smplbt = 60 * sample_rate // (bpm + 5)
        smpltp = 60 * sample_rate // (bpm - 5)
        mx = 0
        ans = 0
        for i in range(len(peaks)):
            st = peaks[i]
            fnd = [False] * peaksneeded
            for j in range(i + 1, len(peaks)):
                for k in range(peaksneeded):
                    if peaks[i] + smpl*k + smplbt < peaks[j] < peaks[i] + smpl*k + smpltp:
                        fnd[k] = True
            good = 0
            for k in range(peaksneeded):
                good += fnd[k]
            if good >= mx:
                ans = i
                mx = good
        return ans

    def ENERGYTACTS(tacts):
        E = []
        for i in range(0, len(tacts)):
            e = CountEnergy(tacts[i], SAMPLEBL)
            E.append(np.array(e))
        return E

    def ENERGYALLTACTS(tacts, group):
        E = []
        for i in range(0, len(tacts), group):
            cur = 0
            for j in range(group):
                if i + j >= len(tacts):
                    break
                for k in tacts[i+j]:
                    cur += k ** 2
            cur /= group * len(tacts[i])
            E.append(cur)
        return E

    def GETFFT(l, r):
        spectrum = np.fft.fft(data[l:r])[:(r-l)//2]
        return spectrum

    def MSE(a):
        return (a**2).mean()

    def CNTERR(a, b):
        #if r + 4*GLSM >= len(data):
        #    return 1e9
        #sa = GETFFT(l, l + 4*GLSM)
        #sb = GETFFT(r, r + 4*GLSM)
        sa = np.ravel(np.array(a))
        sb = np.ravel(np.array(b))
        if len(sa) != len(sb):
            return 1e9
        return MSE(sa-sb)

    def CNTSM(a):
        sa = np.ravel(np.array(a))
        return MSE(sa)
        

    def SIMILAR(E, thres):
        res = []
        for i in range(0, len(E), 4):
            for j in range(i + 4, len(E), 4):
                err = CNTERR(E[i:i+2], E[j:j+2])
                #err = CNTERR(GLST + GLSM*i, GLST + GLSM*j)
                #if (err ** (1/2)) < thres * (((CNTSM(E[i:i+2]) + CNTSM(E[j:j+2]))) ** (1/2)):
                if err < thres:
                    res.append([i, j])
                    res.append([j, i])
        return res

    def DELETENOTTACT(x):
        a = x[0] // 4
        b = x[1] // 4
        return a % 4 != b % 4

    def DELETEDIFEN(x):
        a = x[0] // 4
        b = x[1] // 4
        return False and abs(EALL[a] - EALL[b]) > 0.004

    def DODELETE(x):
        return DELETENOTTACT(x) or DELETEDIFEN(x)

    if LEVADEBIL:
        print("filtering")

    filtered = FILTERBLYAT(data[left:right], 30)
    SAMPLEBL = 1024

    if LEVADEBIL:
        print("energy")

    E = CountEnergy(filtered, SAMPLEBL)
    Elin = np.array(E)

    if LEVADEBIL:
        print("max window")

    mxw = MAXWINDOW(Elin, SAMPLEBL, 20)

    if LEVADEBIL:
        print("piki")

    peaks = FINDPEAKS(mxw, sample_rate // 5, 20)
    BPM = CNTBPM(peaks)
    if LEVADEBIL:
        print("bpm " + str(BPM))

    if LEVADEBIL:
        print("peakToStart")

    peakToStart = GETPEAKSTART(peaks, BPM, 6)

    if LEVADEBIL:
        print("filtering")

    filteredInst = FILTERBLYAT(data, 2000)

    if LEVADEBIL:
        print("tacts")

    tacts, GLST, GLSM = GETTACTS(filteredInst, peaks[peakToStart], BPM)
    tactsRAW, _, _ = GETTACTS(channels, peaks[peakToStart], BPM)

    if LEVADEBIL:
        print("energy tacts")

    EALL = ENERGYALLTACTS(tacts, 4)
    ET = ENERGYTACTS(tacts)

    if LEVADEBIL:
        print("graph")

    GRAPHRAW = SIMILAR(ET, 5000)

    if LEVADEBIL:
        print("last touches")

    GRAPH = [x for x in GRAPHRAW if not DODELETE(x)]

    GRAPH = list(map(lambda x: [(x[0] * GLSM + GLST) / sample_rate, (x[1] * GLSM + GLST) / sample_rate], GRAPH))

    return GRAPH

#sample_rate, channels = wavfile.read("do.wav")
#print(RUNLEVA(sample_rate, channels))
