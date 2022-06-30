/**
 * Copy parent.value in to child.value
 * @param {Element} parent  parent element that contains value
 * @param {Element} child   child element that takes value
 */
export const copy_input = (parent, child) => {
    child.value = parent.value;
};

/**
 * Get or create a paragraph element for containing error text after given id
 * @param {string} id   target element id to look for
 * @returns {Element}   paragraph element after the target
 */
export const get_or_create_error_p = (id) => {
    let elem = document.getElementById(`${id}_error_p`);
    if (elem === null) {
        let input_elem = document.getElementById(id);
        elem = document.createElement('p');
        elem.id = `${id}_error_p`;
        elem.style.display = 'none';
        input_elem.after(elem);
    }
    return elem;
};

/**
 * Set whether the error_p should be displayed or not, if not, the submit button
 * in the form will also be disabled
 * @param {Element} error_p element to be changed
 * @param {boolean} state   state of whether an error had occur
 * @param {string} text     optional, override the error_p innerHTML if given
 */
export const set_error_p = (error_p, state, text = undefined) => {
    if (typeof text !== 'undefined') {
        error_p.innerHTML = text;
    }
    if (state) {
        document.querySelector('button[type="submit"]').disabled = true;
        error_p.style.display = 'block';
    } else {
        document.querySelector('button[type="submit"]').disabled = false;
        error_p.style.display = 'none';
    }
};

/**
 * Check whether username is too short, invalid, or already taken
 * @param {object} event    event to be bounded to
 */
export const check_username = async (event) => {
    let error_flag = false;
    let error_p = get_or_create_error_p('id_username');
    if (event.target.value.length < 3) {
        error_flag = true;
        error_p.innerHTML = 'Username has to be more than 3 characters';
    } else if (!/^\w*$/.test(event.target.value)) {
        error_flag = true;
        error_p.innerHTML = 'Username can only contain letters, numbers, and underscore';
    } else {
        let res = await fetch(`${window.dj_data.urls.users.username_check}?q=${event.target.value}`);
        if (!res.ok) {
            return; // exists w/o error when network fails
        }
        let data = await res.json();
        if (!data.unique) {
            error_flag = true;
            error_p.innerHTML = 'Username taken, please consider:<br>';
            for (let name of data.suggestions) {
                let child_elem = document.createElement('a');
                child_elem.innerHTML = `${name}`;
                child_elem.classList.add('suggestion');
                error_p.appendChild(child_elem);
                error_p.innerHTML += ' ';
            }
        }
    }
    set_error_p(error_p, error_flag);
};

/**
 * Set error state to false and add suggest username to target.value
 * @param {Event} event     event to be bound to
 * @param {Element} target  target elemnt to be changed
 */
export const suggestion_handler = (event, target) => {
    if (event.target.matches('.suggestion')) {
        target.value = event.target.innerHTML;
        set_error_p(get_or_create_error_p('id_username'), false);
    }
};

/**
 * Check whether password2.value is the same as password1.value
 * @param {Element} password1   password1 element
 * @param {Element} password2   password2 element, should have some value as above
 */
export const check_password2 = (password1, password2) => {
    let error_p = get_or_create_error_p('id_password2');
    error_p.innerHTML = 'You must type the same password each time';
    if (password1.value !== password2.value) {
        set_error_p(error_p, true);
    } else {
        set_error_p(error_p, false);
    }
};

/**
 * Display a character count of a textarea element, only when there is text avalialble
 * @param {Event} event         event to be bound to
 */
export const check_textarea_length = (event) => {
    let error_p = get_or_create_error_p(event.target.id);
    if (event.target.value.length === 0) {
        error_p.style.display = 'none';
        return;
    }
    error_p.style.display = 'block';
    error_p.innerHTML = `${event.target.value.length}/${event.target.getAttribute(
        'maxlength'
    )} characters`;
};

/**
 * Check whether the given birth date is for an adult
 * @param {object} event input event on type=input element
 */
export const check_adult = (event) => {
    let error_p = get_or_create_error_p(event.target.id);
    let birthDate = new Date(event.target.value);
    let today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    let m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    if (age < 18) {
        set_error_p(error_p, true, 'You need to be an adult to use rmn_arch_0!');
    } else {
        set_error_p(error_p, false, '');
    }
}
