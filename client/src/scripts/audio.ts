export class Audio {
    private readonly ctx: AudioContext;
    private readonly queue: AudioBuffer[];
    
    public constructor(ctx: AudioContext) {
        this.ctx = ctx;
        this.queue = [];
        this.onChunkEnded = this.onChunkEnded.bind(this);
    }

    public enqueue(chunk: Float32Array): void {
        this.queue.push(this.makeBuffer(chunk));
        if (this.queue.length == 1) {
            this.play();
        }
    }

    private play(): void {
        const source = this.ctx.createBufferSource();
        source.buffer = this.queue[0];
        source.connect(this.ctx.destination);
        source.onended = this.onChunkEnded;
        source.start();
    }

    private onChunkEnded(): void {
        this.queue.pop();
        if (this.queue.length != 0) {
            this.play();
        }
    }

    private makeBuffer(chunk: Float32Array): AudioBuffer {
        const buffer = this.ctx.createBuffer(2, chunk.length, this.ctx.sampleRate);
        buffer.copyToChannel(chunk, 0);
        return buffer;
    }
}
