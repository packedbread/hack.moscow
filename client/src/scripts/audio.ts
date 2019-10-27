export class Audio {
    private readonly ctx: AudioContext;
    private static RAMPING = 1;

    private tracks: AudioBuffer[];
    /** ready to start */
    private nodes: {node: AudioBufferSourceNode, gain: GainNode}[];

    private startAt: number;
    private startTime: number;

    private nowIndex: number;
    private nowPlaying: {node: AudioBufferSourceNode, gain: GainNode};

    private totalDuration: number;
    public onJumpChanged: Function;

    public constructor(ctx: AudioContext) {
        this.ctx = ctx;
        this.tracks = [];
        this.nodes = [];
    }

    public async init(tracks: ArrayBuffer[]): Promise<void> {
        this.nodes.length = this.tracks.length = tracks.length;
        this.totalDuration = 0;
        for (let i = 0; i != tracks.length; ++i) {
            this.tracks[i] = await this.ctx.decodeAudioData(tracks[i]);
            this.nodes[i] = this.recreateSource(i);
            this.totalDuration += this.tracks[i].duration;
        }
        this.jumpTo(0);
        setInterval(() => console.log(this.getTotalTime()), 1000);
    }

    public getWaveforms() {
        return this.tracks.map(buffer => buffer.getChannelData(0));
    }

    jumpTo(time: number) {
        for (let i = 0; i != this.tracks.length; ++i) {
            let duration = this.tracks[i].duration;
            if (time < duration) {
                this.play(i, time);
                break;
            } else {
                time -= duration;
            }
        }
    }

    public scheduleJump(jump: Jump) {
        this.onJumpChanged(jump);
        const now = this.getTotalTime();
        let diff = (jump.from - now) * 1000;
        if (diff < 0) {
            diff += this.totalDuration * 1000;
        }
        let timeout = setTimeout(() => this.jumpTo(jump.to), diff);
        return [diff, timeout];
    }

    public getCurrentTime(): number {
        const now = this.startAt + (this.ctx.currentTime - this.startTime);
        const duration = this.tracks[this.nowIndex].duration;
        return now - Math.floor(now / duration) * duration;
    }

    public getTotalTime(): number {
        let time = 0;
        for (let i = 0; i != this.nowIndex; ++i) {
            time += this.tracks[i].duration;
        }
        return time + this.getCurrentTime();
    }

    public getTrackDuration() {
        return this.tracks[this.nowIndex].duration;
    }

    public getTotalDuration() {
        return this.totalDuration;
    }

    private recreateSource(trackid: number) {
        console.log('creating new Source');
        const sourceNode = this.ctx.createBufferSource();
        sourceNode.loop = false;
        sourceNode.buffer = this.tracks[trackid];
        sourceNode.onended = () => {
            console.log(trackid, 'ended');
            this.play((trackid + 1) % this.tracks.length, 0);
        };
        const gainNode = this.ctx.createGain();
        gainNode.gain.value = 0;
        gainNode.connect(this.ctx.destination);
        sourceNode.connect(gainNode);
        return {node: sourceNode, gain: gainNode};
    }

    private play(index: number, from: number) {
        this.nowIndex = index;
        const oldPlaying = this.nowPlaying;
        [ this.nowPlaying, this.nodes[index] ] = [ this.nodes[index], this.recreateSource(index) ];
        this.startAt = from;
        this.startTime = this.ctx.currentTime;
        this.nowPlaying.node.start(0, from);
        const fadeEndTime = this.startTime + Audio.RAMPING;
        this.nowPlaying.gain.gain.linearRampToValueAtTime(1, fadeEndTime);
        if (oldPlaying) {
            oldPlaying.node.onended = () => {};
            oldPlaying.node.stop(fadeEndTime);
            oldPlaying.gain.gain.linearRampToValueAtTime(0, fadeEndTime);
        }
    }
}
