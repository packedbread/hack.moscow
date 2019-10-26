import 'babel-polyfill';
import {$} from './util';
import {Audio} from './audio';
import {Graphics} from './graphics/graphics';
import {WaveformController} from './graphics/waveform_controller';
import {CaretController} from './graphics/caret_controller';
import {BackgroundController} from './graphics/background_controller';
import {useAudio} from './time';

window.onload = () => {
    input = $('#input');
    button = $('#button');
    timeline = $('#timeline');
    button.onclick = main;
};

const host = '';
const sampleRate = 44100;
const bpm = 128;

var input: HTMLInputElement;
var button: HTMLDivElement;
var timeline: HTMLDivElement;
var audio: Audio;

var caretController: CaretController;
var waveformController: WaveformController;
var graphics: Graphics;

function main() {
    input.onchange = onTrackInput;
    input.click();
}

async function onTrackInput() {
    if (input.files.length == 0) {
        return;
    }
    audio = new Audio(new AudioContext({sampleRate}));
    useAudio(audio);
    graphics = new Graphics(
        caretController = new CaretController(),
        new BackgroundController(),
        waveformController = new WaveformController(sampleRate)
    );
    caretController.setBpm(bpm);
    await audio.init(await Promise.all(
        [...input.files].map(track => new Response(track).arrayBuffer())
    ));
    waveformController.freezeSignals(audio.getWaveforms());
    graphics.startLooping();

    let data = new FormData();
    for (const file of input.files)
        data.append('files[]', file, file.name);
    await fetch('/upload', {
        method: 'POST',
        body: data
    });

    const timeOut = 1000;
    (async function recurr() {
        const response = await jumpRequest(audio.getTotalTime());
        if (response.ok) {
            const json = await response.json();
            console.log('ok', json);
            if (json.ready) {
                button.style.display = 'none';
                timeline.style.display = 'block';
                return doJump(json);
            } else if (json.status === 'merging') {
                button.innerText = 'Merging...';
            } else {
                button.innerText = 'Analyzing...'
            }
        }
        setTimeout(recurr, timeOut);
    })();
}

async function doJump(jump: Jump) {
    if (jump.from < audio.getTotalTime() && jump.to > audio.getTotalTime()) {
        [jump.from, jump.to] = [jump.to, jump.from];
    } else if (jump.from <= audio.getTotalTime() || jump.to >= audio.getTotalTime()) {
        [jump.from, jump.to] = [Math.min(jump.from, jump.to), Math.max(jump.from, jump.to)];
    }
    let timeToJump = audio.scheduleJump(jump);
    waveformController.scheduleJump(jump);
    console.log(timeToJump, jump);
    setTimeout(async () => {
        console.log('requesting');
        doJump(await (await jumpRequest(audio.getTotalTime())).json());
    }, timeToJump);
}

function jumpRequest(time: number) {
    return fetch(host + '/next', {
        method: 'POST',
        body: JSON.stringify({time})
    });
}
