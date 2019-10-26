export class Graphics {
    private readonly controllers: GraphicsController[];

    public constructor(...controllers: GraphicsController[]) {
        this.controllers = controllers;
        this.loop = this.loop.bind(this);
    }

    public startLooping() {
        this.controllers.forEach(controller => controller.init());
        this.loop(0);
    }

    private loop(time: number) {
        this.controllers.forEach(controller => controller.update(time));
        this.controllers.forEach(controller => controller.render());
        requestAnimationFrame(this.loop);
    }
}
