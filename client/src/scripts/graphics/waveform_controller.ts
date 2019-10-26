import { $ } from '../util';

export class WaveformController {
    private readonly sampleRate: number;
    private readonly pixelsPerSec: number;
    private readonly secondsPerBar = 0.1;
    private readonly samplesPerBar: number;
    private readonly pixelsPerBar = 10;

    private readonly canvas: HTMLCanvasElement;

    public constructor(sampleRate: number) {
        this.sampleRate = sampleRate;
        this.samplesPerBar = this.secondsPerBar * this.sampleRate;
        this.pixelsPerSec = this.pixelsPerBar / this.secondsPerBar;

        this.canvas = $('#waveform');
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
