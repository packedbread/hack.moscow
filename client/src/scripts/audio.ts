export class Audio {
    private readonly ctx: AudioContext;

    private tracks: AudioBuffer[];
    /** ready to start */
    private nodes: AudioBufferSourceNode[];

    private startAt: number;
    private startTime: number;

    private nowIndex: number;
    private nowPlaying: AudioBufferSourceNode;

    public constructor(ctx: AudioContext) {
        this.ctx = ctx;
        this.tracks = [];
        this.nodes = [];
    }

    public async init(tracks: ArrayBuffer[]): Promise<void> {
        this.nodes.length = this.tracks.length = tracks.length;
        for (let i = 0; i != tracks.length; ++i) {
            this.tracks[i] = await this.ctx.decodeAudioData(tracks[i]);
            this.nodes[i] = this.recreateSource(i);
        }
        this.jumpTo(0);
        setInterval(() => console.log(this.getCurrentTime()), 1000);
    }

    public getWaveforms() {
        return this.tracks.map(buffer => buffer.getChannelData(0));
    }

    jumpTo(time: number) {
        for (this.nowIndex = 0; this.nowIndex != this.tracks.length; ++this.nowIndex) {
            let duration = this.tracks[this.nowIndex].duration;
            if (time < duration) {
                break;
            } else {
                time -= duration;
            }
        }
        this.play(this.nowIndex, time);
    }

    public scheduleJump(jump: Jump) {
        const now = this.getCurrentTime();
        setTimeout(() => this.jumpTo(jump.to), (this.localize(jump.from) - now) * 1000);
    }

    public getCurrentTime(): number {
        const now = this.startAt + (this.ctx.currentTime - this.startTime);
        const duration = this.tracks[this.nowIndex].duration;
        return now - Math.floor(now / duration) * duration;
    }

    public getTrackDuration() {
        return this.tracks[this.nowIndex].duration;
    }

    private recreateSource(trackid: number) {
        const sourceNode = this.ctx.createBufferSource();
        sourceNode.connect(this.ctx.destination);
        sourceNode.loop = true;
        sourceNode.buffer = this.tracks[trackid];
        sourceNode.onended = () => {
            this.play((trackid + 1) % this.tracks.length, 0);
        }
        return sourceNode;
    }

    private play(index: number, from: number) {
        const oldPlaying = this.nowPlaying;
        [ this.nowPlaying, this.nodes[index] ] = [ this.nodes[index], this.recreateSource(index) ];
        this.startAt = from;
        this.startTime = this.ctx.currentTime;
        this.nowPlaying.start(0, from);
        if (oldPlaying) {
            oldPlaying.onended = () => {};
            oldPlaying.stop();
        }
    }

    private localize(time: number) {
        for (let i = 0; i != this.tracks.length; ++i) {
            if (this.tracks[i].duration > time) {
                return time;
            } else {
                time -= this.tracks[i].duration;
            }
        }
    }
}
