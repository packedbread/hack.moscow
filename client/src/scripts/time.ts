import { Audio } from "./audio";

var audio: Audio;

export function useAudio(_audio: Audio) {
    audio = _audio;
}

/**
 * @returns time since begin of playback, in seconds
 */
export function getTotalTime(): number {
    return audio.getTotalTime();
}

/**
 * @param time since begin of playback, in seconds
 * @returns ratio time / total duration
 */
export function totalRatio(time: number): number {
    return time / audio.getTotalDuration();
}
