import { modal_show, modal_content, set_inner_html } from './modal.js';

/**
 * Check whether user click on a post, load modal if so
 * @param {object} event    document click event
 */
export const get_post = async (event) => {
    if (event.target.matches('.post') && event.button !== 1) {
        event.preventDefault();
        let url = window.dj_data.urls.posts.post_detail_modal;
        url = url.replace(window.dj_data.url_key, event.target.getAttribute('data-uuid'));
        let res = await fetch(url);
        if (!res.ok) {
            modal_content.innerHTML = 'Network Error';
        } else {
            res = await res.text();
            set_inner_html(modal_content, res);
        }
        modal_show();
    }
};
