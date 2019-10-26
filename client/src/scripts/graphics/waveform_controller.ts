import { $ } from '../util';

export class WaveformController {
    private static readonly pxPerBar = 5;
    private static readonly pxPerSec = 30;

    private readonly sampleRate: number;
    private readonly splPerBar: number;

    private readonly waveform: HTMLCanvasElement;

    public constructor(sampleRate: number) {
        this.sampleRate = sampleRate;
        this.splPerBar = sampleRate * WaveformController.pxPerBar / WaveformController.pxPerSec;

        this.waveform = $('#waveform');
    }

    public addChunk(chunk: Float32Array) {
        // TODO
    }

    public update(time: number) {
        // TODO
    }

    public render() {
        // TODO
    }
}
