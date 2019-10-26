import { Audio } from "./audio";

var audio: Audio;

export function useAudio(_audio: Audio) {
    audio = _audio;
}

/**
 * @returns time since begin of song, in seconds
 */
export function getSongTime(): number {
    return audio.getCurrentTime();
}

/**
 * @param time since begin of song, in seconds
 * @returns ratio time / duration of song
 */
export function songRatio(time: number): number {
    return time / audio.getTrackDuration();
}
