export type Fetcher = (time: number) => Promise<Jump>;

export class Audio {
    private readonly ctx: AudioContext;

    private track: AudioBuffer;
    private lastNode: AudioBufferSourceNode;

    private startAt: number;
    private startTime: number;

    public constructor(ctx: AudioContext) {
        this.ctx = ctx;
    }

    public async play(track: ArrayBuffer): Promise<void> {
        this.track = await this.ctx.decodeAudioData(track);
        this.startAt = 0;
        this.startTime = this.ctx.currentTime;
        this.recreateSource(0).start();
    }

    public getWaveform() {
        return this.track.getChannelData(0);
    }

    // public async startJumping(fetcher: Fetcher): Promise<void> {
    //     setInterval(() => console.log(this.getCurrentTime()), 1000);
    //     while (true) {
    //         let { from, to, trackid } = await this.getJump(fetcher);
    //         await this.wait((from - this.getCurrentTime()) * 1000);
    //         const oldNode = this.lastNode;
    //         this.recreateSource(trackid).start(0, to);
    //         oldNode.stop();
    //         this.startTime = this.ctx.currentTime;
    //         this.startAt = to;
    //     }
    // }

    public scheduleJump(jump: Jump) {
        // TODO
    }

    public getCurrentTime(): number {
        const now = this.startAt + (this.ctx.currentTime - this.startTime);
        return now - Math.floor(now / this.track.duration) * this.track.duration;
    }

    public getTrackDuration() {
        return this.track.duration;
    }

    private recreateSource(trackid: number) {
        const sourceNode = this.ctx.createBufferSource();
        sourceNode.connect(this.ctx.destination);
        sourceNode.loop = true;
        sourceNode.buffer = this.track;
        return this.lastNode = sourceNode;
    }

    // private async getJump(fetcher: Fetcher, retry = 2): Promise<Jump> {
    //     let { from, to, trackid } = await fetcher(this.getCurrentTime());
    //     console.log(from, to);
    //     if (from < this.getCurrentTime()) {
    //         [ to, from ] = [ from, to ];
    //     }
    //     if (from - this.getCurrentTime() > 30 && retry > 0) {
    //         return this.getJump(fetcher, retry - 1);
    //     }
    //     return { from, to, trackid };
    // }

    // private wait(millis: number) {
    //     console.log(`waiting ${millis} millis`);
    //     return new Promise(resolve => setTimeout(resolve, millis));
    // }
}
