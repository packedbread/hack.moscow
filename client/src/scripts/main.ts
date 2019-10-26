import {Audio} from './audio';
import {Graphics} from './graphics/graphics';
import {BackgroundController} from './graphics/background_controller';
import {WaveformController} from './graphics/waveform_controller';
import {$} from './util';

window.onload = () => {
    $('#button').onclick = main;
};

const host = 'http://10.0.0.103:5000';
const url = 'http://localhost:5000/audio';
const sampleRate = 44100;
const bpm = 120;

async function fetchChunk(ctx: AudioContext) {
    let res = await fetch(url);
    if (res.status !== 200) {
        console.log('Fetch error:', await res.text());
        return null;
    }
    let buff = await res.arrayBuffer();
    return ctx.decodeAudioData(buff);
}

async function main() {
    let resolve = null;
    let promise = new Promise(r => resolve = r);
    $('#input').addEventListener('change', resolve, false);
    $('#input').click();
    $('#button').innerText = 'Processing...';
    const ctx = new AudioContext({sampleRate});
    await promise;
    let files = $('#input').files;

    // let buff = await ctx.decodeAudioData(await files[0].arrayBuffer());
    // console.log(buff);

    await fetch(host + '/upload', {
        method: 'POST',
        body: await files[0].arrayBuffer(),
    });

    // while (true) {
    //     let res = await fetch(host + '/edges');
    // }

    // const audio = new Audio(ctx);
    // const background = new BackgroundController();
    // const waveform = new WaveformController(sampleRate);
    // const graphics = new Graphics({ sampleRate, bpm, background, waveform });
    // graphics.startLooping();
    // audio.enqueueBuffer(await fetchChunk(ctx));
}
