export class CaretController implements GraphicsController {
    bpm: number;

    constructor(bpm: number) {
        this.bpm = bpm;
    }

    public init(): void {
        document.body.style.setProperty('--bpm', this.bpm.toString());
    }
    
    public update(delta: number): void {
        //
    }

    public render(): void {
        //
    }
}
