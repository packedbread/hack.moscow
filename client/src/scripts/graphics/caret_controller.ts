export class CaretController implements GraphicsController {
    public setBpm(bpm: number) {
        document.body.style.setProperty('--bpm', bpm.toString());
    }

    public init(): void {}
    public update(delta: number): void {}
    public render(): void {}
}
