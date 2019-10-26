import 'babel-polyfill';
import { $ } from './util';
import { Audio } from './audio';
import { Graphics } from './graphics/graphics';
import { WaveformController } from './graphics/waveform_controller';
import { CaretController } from './graphics/caret_controller';
import { BackgroundController } from './graphics/background_controller';
import { useAudio } from './time';

window.onload = () => {
    input = $('#input');
    button = $('#button');
    timeline = $('#timeline');
    button.onclick = main;
};

const host = 'http://10.0.0.103:5000';
const sampleRate = 44100;
const bpm = 128;

var input: HTMLInputElement;
var button: HTMLDivElement;
var timeline: HTMLDivElement;

var audio: Audio;

var caretController: CaretController;
var waveformController: WaveformController;
var graphics: Graphics;

async function main() {
    input.onchange = onTrackInput;
    input.click();
    button.innerText = 'Processing...';
}

async function onTrackInput() {
    if (input.files.length == 0) {
        return;
    }
    button.style.display = 'none';
    timeline.style.display = 'block';
    audio = new Audio(new AudioContext({ sampleRate }));
    useAudio(audio);
    graphics = new Graphics(
        caretController = new CaretController(),
        new BackgroundController(),
        waveformController = new WaveformController(sampleRate)
    );
    caretController.setBpm(bpm);
    await audio.play(await new Response(input.files[0]).arrayBuffer());
    waveformController.freezeSignal(audio.getWaveform());
    graphics.startLooping();
    console.log(input.files[0]);
    await fetch(host + '/upload', {
        method: 'POST',
        body: input.files[0],
    });
    const timeOut = 1000;
    (async function recurr() {
        const response = await fetch(host + '/next', {
            method: 'POST',
            body: JSON.stringify({ current_time: 0 })
        });
        console.log(response);
        if (response.ok) {
            startJumping();
        } else {
            setTimeout(recurr, timeOut);
        }
    })();
}

async function startJumping() {
    audio.startJumping(async current_time =>
        (await fetch(host + '/next', {
            method: 'POST',
            body: JSON.stringify({ current_time })
        })).json()
    );
}
