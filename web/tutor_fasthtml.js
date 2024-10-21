// get url info
function get_url() {
    const url = document.getElementById('url').value;
    return {session_id, url};
}

// get context from current row
function get_context() {
    const query = document.getElementById('query').value;
    const row_box = document.querySelector('.lang-row.active');
    const orig_box = row_box.querySelector('.lang-orig');
    const trans_box = row_box.querySelector('.lang-trans');
    const orig = orig_box?.textContent ?? null;
    const trans = trans_box?.textContent ?? null;
    return {session_id, query, orig, trans};
}

function scroll_to(target) {
    if (typeof target == 'number') {
        const trans = document.getElementById('lang-scroll');
        trans.scrollTo({top: target, behavior: 'smooth'});
    } else {
        target.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    }
}

// global keydown event
document.addEventListener('keydown', (event) => {
    // suppress enter key in url input
    if (event.key === 'Enter' && event.target.id === 'url') {
        event.preventDefault();
    }

    // cursor control up/down
    if (event.key === 'ArrowDown') {
        const pane = document.getElementById('lang-pane');
        const active = pane.querySelector('.lang-row.active');
        const next = active.nextElementSibling;
        if (next == null) {
            return;
        }
        active.classList.remove('active');
        next.classList.add('active');
        if (next.id == 'row-last') {
            scroll_to(trans.scrollHeight);
        } else {
            scroll_to(next);
        }
        event.preventDefault();
    } else if (event.key === 'ArrowUp') {
        const pane = document.getElementById('lang-pane');
        const active = pane.querySelector('.lang-row.active');
        const prev = active.previousElementSibling;
        if (prev == null) {
            return;
        }
        active.classList.remove('active');
        prev.classList.add('active');
        if (prev.id == 'row-first') {
            scroll_to(0);
        } else {
            scroll_to(prev);
        }
        event.preventDefault();
    }
});

// cursor control click
document.addEventListener('click', (event) => {
    const pane = document.getElementById('lang-pane');
    const row = event.target.closest('.lang-row');
    if (row == null || row.classList.contains('active')) {
        return;
    }
    const active = pane.querySelector('.lang-row.active');
    if (active != null) {
        active.classList.remove('active');
    }
    row.classList.add('active');
    scroll_to(row);
    event.preventDefault();
});

// handle websocket events - translation progress
document.addEventListener('htmx:wsBeforeMessage', event => {
    const message = event.detail.message;
    if (message == 'LANGTUTOR_START') {
        const button = document.getElementById('translate');
        const query = document.getElementById('query');
        console.log('langtutor start');
        button.textContent = 'Translating...';
        button.disabled = true;
        query.disabled = true;
    } else if (message == 'LANGTUTOR_DONE') {
        const button = document.getElementById('translate');
        const query = document.getElementById('query');
        console.log('langtutor done');
        button.textContent = 'Translate';
        button.disabled = false;
        query.disabled = false;
    }
});
