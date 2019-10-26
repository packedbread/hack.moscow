import { $ } from '../util';

export class BackgroundController {
    private readonly background: HTMLCanvasElement;

    public constructor() {
        this.background = $('#background');
        this.whenSegmentEnds = this.whenSegmentEnds.bind(this);
    }

    public whenSegmentEnds() {
        // TODO transmission animation
    }

    public update(time: number) {
        // TODO
    }

    public render() {
        // TODO
    }
}
