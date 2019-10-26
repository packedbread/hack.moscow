import { BackgroundController } from './background_controller';
import { WaveformController } from './waveform_controller';

export type GraphicsOptions = {
    bpm: number;
    background: BackgroundController;
    waveform: WaveformController;
}

export class Graphics {
    private readonly bpm: number;
    private readonly background: BackgroundController;
    private readonly waveform: WaveformController;

    public constructor({ bpm, background, waveform }: GraphicsOptions) {
        this.bpm = bpm;

        this.background = background;
        this.waveform = waveform;

        this.loop = this.loop.bind(this);
    }

    public startLooping() {
        document.body.style.setProperty('--bpm', this.bpm.toString());
        requestAnimationFrame(this.loop);
    }

    private loop(time: number) {
        this.background.update(time);
        this.waveform.update(time);

        this.background.render();
        this.waveform.render();
    }
}
