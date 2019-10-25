import { Audio } from './audio';

document.onload = main;

function main() {
    const audio = new Audio(new AudioContext({ sampleRate: 44100 }));
}
