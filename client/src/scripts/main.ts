import 'babel-polyfill';
import {$} from './util';
import {Audio} from './audio';

window.onload = () => {
    input = $('#input');
    button = $('#button');
    timeline = $('#timeline');
    button.onclick = main;
};

const host = 'http://10.0.0.103:5000';
const sampleRate = 44100;

var input: HTMLInputElement;
var button: HTMLDivElement;
var timeline: HTMLDivElement;
var audio: Audio;

async function main() {
    input.onchange = onTrackInput;
    input.click();
}

async function onTrackInput() {
    if (input.files.length == 0) {
        return;
    }
    button.innerText = 'Processing...';
    audio = new Audio(new AudioContext({sampleRate}));
    audio.play(await new Response(input.files[0]).arrayBuffer());

    if (input.files.length == 1) {
        // OLD VERSION (ONE FILE)
        console.log(input.files[0]);
        await fetch(host + '/upload', {
            method: 'POST',
            body: input.files[0],
        });
    } else {
        // NEW VERSION (MULTIPLE FILES)
        let data = new FormData();
        for (const file of input.files)
            data.append('files[]', file, file.name);
        await fetch('/upload', {
            method: 'POST',
            body: data
        });
    }

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
    button.style.display = 'none';
    timeline.style.display = 'absolute';
    audio.startJumping(async current_time =>
        (await fetch(host + '/next', {
            method: 'POST',
            body: JSON.stringify({ current_time })
        })).json()
    );
}
