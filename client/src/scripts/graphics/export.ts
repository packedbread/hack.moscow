import { Graphics } from "./graphics";
import { CaretController } from "./caret_controller";
import { BackgroundController } from "./background_controller";
import { WaveformController } from "./waveform_controller";

export function buildGraphics(bpm: number, sampleRate: number) {
    return new Graphics(
        new CaretController(bpm),
        new BackgroundController(),
        new WaveformController(sampleRate)
    );
}
