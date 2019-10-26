import { Audio } from './audio';

document.onload = main;

const url = 'http://box-server.herokuapp.com/from1to1';
const sampleRate = 44100;

async function fetchChunk() {
    let res = await fetch(url);
    let buff = await res.arrayBuffer();
    return new Float32Array(buff);
}

function main() {
    const ctx = new AudioContext({ sampleRate });
    const audio = new Audio(ctx);
}
