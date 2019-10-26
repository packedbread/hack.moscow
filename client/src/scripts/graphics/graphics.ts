import { BackgroundController } from './background_controller';
import { WaveformController } from './waveform_controller';

export type GraphicsOptions = {
    sampleRate: number;
    bpm: number;
    background: BackgroundController;
    waveform: WaveformController;
}

export class Graphics {
    private static readonly delta = 1;

    private readonly bpm: number;
    private readonly sampleRate: number;

    private readonly background: BackgroundController;
    private readonly waveform: WaveformController;

    public constructor({ sampleRate, bpm, background, waveform }: GraphicsOptions) {
        this.bpm = bpm;
        this.sampleRate = sampleRate;

        this.background = background;
        this.waveform = waveform;

        this.onChunkChanged = this.onChunkChanged.bind(this);
        this.loop = this.loop.bind(this);
    }

    public startLooping() {
        document.body.style.setProperty('--bpm', this.bpm.toString());
        requestAnimationFrame(this.loop);
    }

    public onChunkChanged(chunkLength: number) {
        setTimeout(
            this.background.whenSegmentEnds,
            (chunkLength / this.sampleRate - Graphics.delta) * 1000
        );
    }

    private loop(time: number) {
        this.background.update(time);
        this.waveform.update(time);

        this.background.render();
        this.waveform.render();
    }
}
