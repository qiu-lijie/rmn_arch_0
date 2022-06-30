// Simple modal and manipulation, requires modal be in the document

const body = document.querySelector('body');
const modal = document.querySelector('.modal');
export const modal_content = document.querySelector('.modal-content');

// show the model
export const modal_show = () => {
    modal.style.display = 'flex';
    body.style.overflow = 'hidden';
};

// hide the model
export const modal_hide = () => {
    modal.style.display = 'none';
    body.style.overflow = 'auto';
};

// change innerHTML then run any script attached
export const set_inner_html = function (elem, html) {
    elem.innerHTML = html;
    Array.from(elem.querySelectorAll('script')).forEach((oldScript) => {
        const newScript = document.createElement('script');
        Array.from(oldScript.attributes).forEach((attr) =>
            newScript.setAttribute(attr.name, attr.value)
        );
        newScript.appendChild(document.createTextNode(oldScript.innerHTML));
        oldScript.parentNode.replaceChild(newScript, oldScript);
    });
};

// close modal when click out side of modal-content
document.addEventListener(
    'click',
    (event) => {
        if (event.target.matches('.modal') || event.target.matches('.close')) {
            modal_hide();
        }
    },
    false
);
