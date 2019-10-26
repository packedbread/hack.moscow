import { Audio } from './audio';
import { Graphics } from './graphics/graphics';
import { BackgroundController } from './graphics/background_controller';
import { WaveformController } from './graphics/waveform_controller';

window.onload = main;

const sampleRate = 44100;
const bpm = 120;

function main() {
    const audio = new Audio(new AudioContext({ sampleRate }));
    const background = new BackgroundController();
    const waveform = new WaveformController(sampleRate);
    const graphics = new Graphics({ sampleRate, bpm, background, waveform });
    graphics.startLooping();
}
