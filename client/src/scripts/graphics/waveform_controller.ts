import * as PIXI from 'pixi.js';
import { $ } from '../util';
import { songRatio, getSongTime } from '../time';

export class WaveformController implements GraphicsController {
    private readonly sampleRate: number;
    private readonly secondsPerBar = 0.1;
    private readonly samplesPerBar: number;
    private readonly pixelsPerBar = 10;
    private readonly borderRadius = 4;
    private readonly barPadding = 1;

    private readonly canvas: HTMLCanvasElement;
    private readonly pixiApp: PIXI.Application;

    private bars: number[];
    private barGraphics: PIXI.Container;

    public constructor(sampleRate: number) {
        this.sampleRate = sampleRate;
        this.samplesPerBar = this.secondsPerBar * this.sampleRate;

        this.canvas = $('#waveform');
        this.pixiApp = new PIXI.Application({
            view: this.canvas
        });
    }

    public freezeSignal(signal: Float32Array) {
        let bars = [];
        let max = -Infinity;
        for (let i = 0; i < signal.length; i += this.samplesPerBar) {
            let window = signal.slice(i, i + this.samplesPerBar);
            let volume = window.reduce((acc, x) => acc + Math.abs(x));
            volume = volume / window.length;
            bars.push(volume);
            max = Math.max(max, volume);
        }
        this.bars = bars.map(bar => bar / max);
    }

    init() {
        const black = new PIXI.Graphics(), gray = new PIXI.Graphics();
        black.beginFill(0xffffff);
        gray.beginFill(0x666666)
        for (let i = 0; i != this.bars.length; ++i) {
            const x = this.pixelsPerBar * i + this.barPadding, mid = this.canvas.height / 2;
            const width = this.pixelsPerBar - this.barPadding * 2,
                  height = mid * this.bars[i];
            black.drawRoundedRect(x, mid - height, width, height, this.borderRadius);
            gray.drawRoundedRect(x, mid, width, height, this.borderRadius);
        }
        black.endFill();
        gray.endFill();
        const container = new PIXI.Container();
        container.addChild(black, gray);
        this.pixiApp.stage.addChild(container);
        this.barGraphics = container;
    }

    public update(_: number) {
        const ratio = songRatio(getSongTime());
        const graphicsWidth = this.bars.length * this.pixelsPerBar;
        this.barGraphics.x = this.canvas.width * 0.5 - graphicsWidth * ratio;
    }

    public render() {
        this.pixiApp.render();
    }
}
