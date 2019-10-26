export type Jump = { from: number, to: number };

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
        this.recreateSource().start();
    }

    public async startJumping(fetcher: Fetcher): Promise<void> {
        setInterval(() => console.log(this.getTime()), 1000);
        while (true) {
            let { from, to } = await this.getJump(fetcher);
            await this.wait((from - this.getTime()) * 1000);
            const oldNode = this.lastNode;
            this.recreateSource().start(0, to);
            oldNode.stop();
            this.startTime = this.ctx.currentTime;
            this.startAt = to;
        }
    }

    private recreateSource() {
        const sourceNode = this.ctx.createBufferSource();
        sourceNode.connect(this.ctx.destination);
        sourceNode.loop = true;
        sourceNode.buffer = this.track;
        return this.lastNode = sourceNode;
    }

    private async getJump(fetcher: Fetcher, retry = 2): Promise<Jump> {
        let { from, to } = await fetcher(this.getTime());
        console.log(from, to);
        if (from < this.getTime()) {
            [ to, from ] = [ from, to ];
        }
        if (from - this.getTime() > 30 && retry > 0) {
            return this.getJump(fetcher, retry - 1);
        }
        return { from, to };
    }

    private getTime(): number {
        const now = this.startAt + (this.ctx.currentTime - this.startTime);
        return now - Math.floor(now / this.track.duration) * this.track.duration;
    }

    private wait(millis: number) {
        console.log(`waiting ${millis} millis`);
        return new Promise(resolve => setTimeout(resolve, millis));
    }
}
