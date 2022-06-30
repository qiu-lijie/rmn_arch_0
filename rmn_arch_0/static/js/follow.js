const ACTIVE = 'active';

/**
 * Handles follow event, requires
 *      element to be bound to has data-username
 * @param {object} event        event to be bound to
 */
export const follow = async (event) => {
    event.target.classList.add('disabled');
    document.querySelectorAll('.follow-icon').forEach((elem) => {
        elem.classList.toggle(ACTIVE);
    });
    let follow = event.target.classList.contains(ACTIVE);
    let username = event.target.getAttribute('data-username');
    let res = await fetch(window.dj_data.urls.users.follow, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.dj_data.csfr_token,
        },
        body: JSON.stringify({
            username: username,
            follow: follow,
        }),
    });
    if (!res.ok) {
        event.target.style.backgroundImage = 'none';
        event.target.style.width = 'unset';
        event.target.innerHTML = 'Network Error';
        return;
    }
    event.target.classList.remove('disabled');
};
