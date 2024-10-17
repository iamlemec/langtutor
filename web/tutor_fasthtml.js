// get context from current row
function get_context() {
    const query = document.getElementById('query').value;
    const row = document.querySelector('.lang-row.active');
    const orig = row.querySelector('.lang-orig');
    const trans = row.querySelector('.lang-trans');
    return {query: query, orig: orig.textContent, trans: trans.textContent};
}

// global keydown event
document.addEventListener('keydown', (event) => {
    // suppress enter key in url input
    if (event.key === 'Enter' && event.target.id === 'url') {
        event.preventDefault();
    }

    // cursor control up/down
    if (event.key === 'ArrowDown') {
        const active = document.querySelector('.lang-row.active');
        const next = active.nextElementSibling;
        if (next == null) {
            return;
        }
        active.classList.remove('active');
        next.classList.add('active');
        if (next.id == 'row-last') {
            const trans = document.getElementById('trans');
            trans.scrollTo({top: trans.scrollHeight, behavior: 'smooth'});
        } else {
            next.scrollIntoView({behavior: 'smooth', block: 'nearest'});
        }
        event.preventDefault();
    } else if (event.key === 'ArrowUp') {
        const active = document.querySelector('.lang-row.active');
        const prev = active.previousElementSibling;
        if (prev == null) {
            return;
        }
        active.classList.remove('active');
        prev.classList.add('active');
        if (prev.id == 'row-first') {
            const trans = document.getElementById('trans');
            trans.scrollTo({top: 0, behavior: 'smooth'});
        } else {
            prev.scrollIntoView({behavior: 'smooth', block: 'nearest'});
        }
        event.preventDefault();
    }
});

// cursor control click
document.addEventListener('click', (event) => {
    const row = event.target.closest('.lang-row');
    if (row == null || row.classList.contains('active')) {
        return;
    }
    const active = document.querySelector('.lang-row.active');
    if (active != null) {
        active.classList.remove('active');
    }
    row.classList.add('active');
    row.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    event.preventDefault();
});

// handle websocket events - translation progress
document.addEventListener('htmx:wsBeforeMessage', event => {
    const message = event.detail.message;
    const button = document.querySelector('#translate');
    if (message == 'LANGTUTOR_FETCHING') {
        button.textContent = 'Fetching...';
        button.disabled = true;
    } else if (message == 'LANGTUTOR_EXTRACTING') {
        button.textContent = 'Extracting...';
        button.disabled = true;
    } else if (message == 'LANGTUTOR_TRANSLATING') {
        button.textContent = 'Translating...';
        button.disabled = true;
    } else if (message == 'LANGTUTOR_DONE') {
        button.textContent = 'Translate';
        button.disabled = false;
    }
});
