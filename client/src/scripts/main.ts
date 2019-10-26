import { $ } from './util';
import { Audio } from './audio';

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
    button.innerText = 'Processing...';
}

async function onTrackInput() {
    if (input.files.length == 0) {
        return;
    }
    audio = new Audio(new AudioContext({ sampleRate }));
    audio.play(await new Response(input.files[0]).arrayBuffer());
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
    button.hidden = true;
    timeline.hidden = false;
    audio.startJumping(async current_time =>
        (await fetch(host + '/next', {
            method: 'POST',
            body: JSON.stringify({ current_time })
        })).json()
    );
}
