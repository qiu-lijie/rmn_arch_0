export const Carousel = class {
    constructor() {
        this.curr_index = 0;
        this.slides = document.getElementsByClassName('carousel-cell');
        this.dots = document.getElementsByClassName('dot');
        this.len = this.slides.length;
        this.x0 = null;

        document.querySelector('.next').addEventListener(
            'click',
            () => {
                this.show_slide(this.curr_index + 1);
            },
            false
        );
        document.querySelector('.prev').addEventListener(
            'click',
            () => {
                this.show_slide(this.curr_index - 1);
            },
            false
        );
        document.querySelectorAll('.dot').forEach((elem) => {
            elem.addEventListener(
                'click',
                (event) => {
                    this.show_slide(parseInt(event.target.getAttribute('data-index')));
                },
                false
            );
        });
        let carousel = document.querySelector('.carousel');
        carousel.addEventListener(
            'mousedown',
            (event) => {
                this.lock(event);
            },
            false
        );
        carousel.addEventListener(
            'touchstart',
            (event) => {
                this.lock(event);
            },
            false
        );
        carousel.addEventListener(
            'mouseup',
            (event) => {
                this.move(event);
            },
            false
        );
        carousel.addEventListener(
            'touchend',
            (event) => {
                this.move(event);
            },
            false
        );

        this.show_slide(this.curr_index);
    }

    unify(event) {
        return event.changedTouches ? event.changedTouches[0] : event;
    }

    lock(event) {
        this.x0 = this.unify(event).clientX;
    }

    move(event) {
        if (this.x0 || this.x0 === 0) {
            let movement = Math.sign(this.unify(event).clientX - this.x0);
            this.show_slide(this.curr_index - movement);
        }
    }

    /**
     * show the given carousel cell, warp if out of range
     * @param {number} n    index of the carousel cell to show
     */
    show_slide(n) {
        this.curr_index = n;
        if (n >= this.len) {
            this.curr_index = 0;
        } else if (n < 0) {
            this.curr_index = this.len - 1;
        }
        for (let i = 0; i < this.len; i++) {
            this.slides[i].classList.toggle('active', this.curr_index === i);
            this.dots[i].classList.toggle('active', this.curr_index === i);
        }
    }
};
