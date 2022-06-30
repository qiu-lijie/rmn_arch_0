/**
 * Paginator object, requires
 *  two views, first handle initial request, second handle subsequent ones
 *  #paginate_hook exposed in inner template being paginated containing whether there is a next page
 * @param {string} paginated_url    url to get following pages
 * @param {number} scroll_bottom    px from button of scroll_obj to load next page
 *                                  defaults to 250
 * @param {object} scorll_obj       object to attach scroll eventlistener to
 *                                  defaults to document
 * @param {string} paginate_hook    id of paginate_hook, where the paginated content will be loaded
 *                                  and contains whether there is a next page
 *                                  defaults to 'paginate_hook'
 */
export const Paginator = class {
    constructor(
        paginated_url,
        scroll_bottom = 250,
        scorll_obj = document,
        paginate_hook = 'paginate_hook'
    ) {
        this.page = 2; // django pagination is 1-based indexed, second page is 2
        this.scroll_bottom = scroll_bottom;
        this.scorll_obj = scorll_obj;
        this.paginate_hook = paginate_hook;
        this.more = JSON.parse(document.getElementById(this.paginate_hook).innerHTML);
        this.enabled = true;

        this.scorll_obj.addEventListener(
            'scroll',
            async () => {
                if (
                    this.enabled &&
                    this.more &&
                    this.check_scroll_px_from_bottom() <= this.scroll_bottom
                ) {
                    this.enabled = false;
                    let res = await fetch(`${paginated_url}?page=${this.page}`);
                    if (!res.ok) {
                        if (res.status === 404) {
                            this.more = false;
                        }
                        return; // fail silently
                    } else {
                        const content = document.createElement('div');
                        content.innerHTML = await res.text();
                        const hook = document.getElementById(this.paginate_hook);
                        hook.after(content);
                        hook.remove();
                        content.replaceWith(...content.childNodes);
                        this.more = JSON.parse(
                            document.getElementById(this.paginate_hook).innerHTML
                        );
                        this.page++;
                    }
                    this.enabled = true;
                }
            },
            false
        );
    }

    /**
     * @returns current postion of the scroll bar from the bottom
     */
    check_scroll_px_from_bottom = () => {
        if (this.scorll_obj === document) {
            let body = document.body,
                html = document.documentElement;
            let height = Math.max(
                body.scrollHeight,
                body.offsetHeight,
                html.clientHeight,
                html.scrollHeight,
                html.offsetHeight
            );
            return height - window.innerHeight - window.scrollY;
        } else {
            return (
                this.scorll_obj.scrollHeight -
                this.scorll_obj.scrollTop -
                this.scorll_obj.clientHeight
            );
        }
    };
};
