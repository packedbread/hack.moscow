import {Audio} from "./audio";

export default class Navigator {
    root: HTMLElement;
    cursor: HTMLElement;
    jump: HTMLElement;
    audio: Audio;

    constructor() {
        this.root = document.querySelector('#navigator');
        this.cursor = document.querySelector('#navigator .cursor');
        this.jump = document.querySelector('#navigator .jump');
        this.root.onclick = this.onclick.bind(this);
    }

    onclick(event) {
        let rect = event.target.getBoundingClientRect();
        let pos = (event.clientX - rect.left) / rect.width;
        this.audio.jumpTo(pos * this.audio.getTotalDuration());
    }

    hook(audio: Audio) {
        this.audio = audio;
        setInterval(() => {
            let pos = audio.getTotalTime() / audio.getTotalDuration();
            this.updatePos(pos);
        }, 200);
        audio.onJumpChanged = this.updateJump.bind(this);
    }

    setSignals(signals: Float32Array[]) {
        let lengths = signals.map(x => x.length);
        let total = lengths.reduce((a, b) => a + b);
        let percents = lengths.map(x => Math.round(x / total * 100));

        for (let width of percents) {
            let div = document.createElement('div');
            div.style.width = width + '%';
            this.root.appendChild(div);
        }
    }

    updatePos(pos: number) {
        let percent = Math.round(pos * 100 * 100) / 100;
        let rem = Math.round(pos * 100) / 100;
        this.cursor.style.left = `calc(${percent}% - ${rem}rem)`;
    }

    updateJump(jump: Jump) {
        setTimeout(() => {
            let from = Math.min(jump.from, jump.to);
            let to = Math.max(jump.from, jump.to);
            let left = Math.round(from / this.audio.getTotalDuration() * 100 * 100) / 100;
            let width = Math.round((to - from) / this.audio.getTotalDuration() * 100 * 100) / 100;
            this.jump.style.left = left + '%';
            this.jump.style.width = width + '%';
        }, 500);
    }
}
