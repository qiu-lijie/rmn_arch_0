const RATED = 'rated';
const DATA_RATE = 'data-rate';

/**
 * Add RATED to appropriate locations to show proper highlight of fires
 * @param {Element} data_elem   element thats has DATA_RATE attribute
 * @param {string} rate_val     string representation of the rate value
 */
const change_display_styles = (data_elem, rate_val) => {
    const parent = data_elem.querySelector('.rate-div');
    for (let child of parent.children) {
        if (child.getAttribute(DATA_RATE) === rate_val) {
            child.classList.add(RATED);
        } else {
            child.classList.remove(RATED);
        }
    }
    parent.classList.add(RATED);

    // show other's rating if available
    const avg_rating = data_elem.querySelector('.post-avg-rating');
    if (avg_rating) {
        avg_rating.classList.add(RATED);
    }
};

/**
 * Handles the rate event
 *      Requires data-uuid set on the thrid level parent
 * @param {event} event event to listent to
 */
export const rate = async (event) => {
    if (event.target.matches(`.rate`)) {
        event.preventDefault();
        const elem = event.target;
        const data_elem = elem.parentElement.parentElement.parentElement;
        const uuid = data_elem.getAttribute('data-uuid');
        const rate_val = elem.getAttribute(DATA_RATE);
        if (elem.classList.contains(RATED)) {
            return; // already rated the same rate
        }

        // change display style
        document.querySelectorAll(`*[data-uuid="${uuid}"]`).forEach((elem) => {
            change_display_styles(elem, rate_val);
        });

        // post to server
        let res = await fetch(window.dj_data.urls.posts.rate, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.dj_data.csfr_token,
            },
            body: JSON.stringify({
                uuid: uuid,
                rate: rate_val,
            }),
        });
        if (!res.ok) {
            return; // return w/o error when network failed
        }
        // successed!
    }
};
