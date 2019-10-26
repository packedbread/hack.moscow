import { $ } from '../util';

export class WaveformController implements GraphicsController {
    private readonly sampleRate: number;
    private readonly pixelsPerSec: number;
    private readonly secondsPerBar = 0.1;
    private readonly samplesPerBar: number;
    private readonly pixelsPerBar = 10;

    private readonly canvas: HTMLCanvasElement;

    private bars: number[];

    public constructor(sampleRate: number) {
        this.sampleRate = sampleRate;
        this.samplesPerBar = this.secondsPerBar * this.sampleRate;
        this.pixelsPerSec = this.pixelsPerBar / this.secondsPerBar;

        this.canvas = $('#waveform');
    }

    // Converts signal to
    public freezeSignal(signal: Float32Array) {
        let bars = [];
        for (let i = 0; i < signal.length; i += this.samplesPerBar) {
            let window = signal.slice(i, i + this.samplesPerBar);
            let volume = window.reduce((acc, x) => acc + Math.abs(x));
            volume = Math.log10(volume / window.length);
            bars.unshift(volume);
        }
        this.bars = bars;
    }

    init() {
        //
    }

    public update(time: number) {
        // TODO
    }

    public render() {
        // TODO
    }
}
