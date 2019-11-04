import * as PIXI from 'pixi.js';
import { $ } from '../util';
import { totalRatio, getTotalTime } from '../time';

export class WaveformController implements GraphicsController {
    private readonly sampleRate: number;
    private readonly secondsPerBar = 0.1;
    private readonly samplesPerBar: number;
    private readonly pixelsPerBar = 10;
    private readonly barPadding = 1;

    private readonly canvas: HTMLCanvasElement;

    private pixiApp: PIXI.Application;
    private bars: number[];

    public constructor(sampleRate: number) {
        this.sampleRate = sampleRate;
        this.samplesPerBar = this.secondsPerBar * this.sampleRate;

        this.canvas = $('#waveform');

        this.resizeCanvas = this.resizeCanvas.bind(this);
        this.pixiApp = new PIXI.Application({
            view: this.canvas,
            antialias: true,
            transparent: true
        });

        this.freezeSignal = this.freezeSignal.bind(this);
    }

    public freezeSignals(signals: Float32Array[]) {
        this.bars = signals
                .map(x => this.freezeSignal(x))
                .reduce((bars, x) => {
                    bars.push(...x);
                    return bars;
                });
        console.log(this.bars);
    }

    private freezeSignal(signal: Float32Array) {
        let bars = [];
        let max = -Infinity;
        for (let i = 0; i < signal.length; i += this.samplesPerBar) {
            let window = signal.slice(i, i + this.samplesPerBar);
            let volume = window.reduce((acc, x) => acc + Math.abs(x));
            volume = volume / window.length;
            bars.push(volume);
            max = Math.max(max, volume);
        }
        return bars.map(bar => bar / max);
    }

    init() {
        window.addEventListener('resize', this.resizeCanvas);
        this.resizeCanvas();
        const barsInGraphics = Math.floor(Math.sqrt(this.bars.length));
        const totalWidth = this.pixelsPerBar * this.bars.length;
        const radius = this.pixelsPerBar / 2 - this.barPadding;
        const width = this.pixelsPerBar - this.barPadding * 2;
        for (let gr = 0; gr <= this.bars.length / barsInGraphics; ++gr) {
            const bars = new PIXI.Graphics();
            for (let j = 0; j != barsInGraphics; ++j) {
                const i = gr * barsInGraphics + j;
                if (i >= this.bars.length) {
                    break;
                }
                const x = this.pixelsPerBar * i + this.barPadding;
                const height = Math.max(this.canvas.height * this.bars[i], radius * 2);
                const y = (this.canvas.height - height) / 2;
                // if (height < radius * 2) continue;
                bars.beginFill(this.getColor(this.bars[i]));
                bars.drawRoundedRect(x, y, width, height, radius);
                bars.drawRoundedRect(x + totalWidth, y, width, height, radius);
                bars.drawRoundedRect(x - totalWidth, y, width, height, radius);
                bars.endFill();
            }
            this.pixiApp.stage.addChild(bars);
        }
    }

    public scheduleJump(jump: Jump) {
        // TODO
    }

    public update(_: number) {
        const ratio = totalRatio(getTotalTime());
        const graphicsWidth = this.bars.length * this.pixelsPerBar;
        this.pixiApp.stage.x = this.canvas.width * 0.5 - graphicsWidth * ratio;
    }

    public render() {
        this.pixiApp.render();
    }

    private resizeCanvas() {
        const { width, height } = this.canvas.getBoundingClientRect();
        console.log(width, height);
        this.pixiApp.renderer.resize(width, height);
    }

    private getColor(ratio: number) {
        return 0xffffff;
    }
}
