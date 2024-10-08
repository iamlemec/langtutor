# fasthtml language tutor

import os
import uvicorn
from uvicorn.supervisors import ChangeReload
import fire

from fasthtml.common import *
from oneping.chat.fasthtml import chat_css, chat_js, ChatWindow, websocket
from translate import LangChat

##
## components
##

def UrlInput():
    url = Input(
        cls='w-full p-2 font-mono text-sm outline-none border-b border-gray-300 bg-gray-100',
        placeholder='Enter a URL', hx_get='/article', name='url'
    )
    return Form(hx_post='/article', hx_target='#lang-pane', hx_swap='outerHTML')(url)

def LangRow(orig, trans, cls=''):
    orig = Div(cls='lang-orig w-full')(Span(orig))
    trans = Div(cls='lang-trans w-full')(Span(trans))
    return Div(cls=f'lang-row w-full flex flex-col border rounded-sm p-2 gap-2 {cls}')(orig, trans)

def LangPane(texts=None):
    if texts is None:
        texts = []
    first = Div(id='row-first', cls='lang-row hidden active')
    last = Div(id='row-last', cls='lang-row hidden')
    return Div(id='lang-pane', cls='w-full flex flex-col gap-2 p-2')(
        first, *[LangRow(orig, trans) for orig, trans in texts], last
    )

def LangTutor(provider='local', model=None):
    # make chat interface
    chat = LangChat(provider=provider, model=model)

    # create app object
    hdrs = [
        Script(src="https://cdn.tailwindcss.com"),
        Script(src='https://cdn.jsdelivr.net/npm/marked/marked.min.js')
    ]
    app = FastHTML(hdrs=hdrs, ws_hdr=True, debug=True, live=True)

    script_cursor = Script("""
    function get_cursor() {
        const row = document.querySelector('.lang-row.active');
        const orig = row.querySelector('.lang-orig');
        const trans = row.querySelector('.lang-trans');
        return {orig: orig.textContent, trans: trans.textContent};
    }
    document.addEventListener('keydown', (event) => {
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
    """)

    style_cursor = Style("""
    .lang-row.active {
        border-color: #60a5fa;
    }
    .lang-row.active ~ .lang-row > .lang-trans {
        border-radius: 0.25rem;
    }
    .lang-row.active ~ .lang-row > .lang-trans > span {
        color: #e5e7eb;
        background-color: #e5e7eb;
    }
    """)

    # connect main
    @app.get('/')
    def index():
        # chat style and script
        style, script = Style(chat_css), Script(chat_js)

        # window title
        title = Title('LangTutor')

        # lang and chat window
        lang = LangPane()
        url = UrlInput()
        hist = ChatWindow(hx_vals='js:{...get_cursor()}')
        trans = Div(id='trans', cls='h-full overflow-y-scroll')(lang)

        # panes and body
        left = Div(cls='h-full w-[70%] flex flex-col border-r border-gray-300')(url, trans)
        right = Div(cls='h-full w-[30%] overflow-y-scroll bg-gray-100')(hist)
        body = Body(cls='h-screen w-screen flex flex-row')(left, right)

        # return
        return (title, style, style_cursor, script, script_cursor), body

    # get article
    @app.post('/article')
    async def article(url: str):
        print(f'/article: {url}')
        chat.set_article(url)
        return LangPane(chat.texts)

    # connect websocket
    @app.ws('/generate')
    async def generate(prompt: str, orig: str, trans: str, send):
        print(f'GENERATE: {prompt}')
        print(f'ORIG: {orig}')
        print(f'TRANS: {trans}')
        stream = chat.stream_query(orig, trans, prompt)
        await websocket(prompt, stream, send)
        print('\nDONE')

    # return
    return app

##
## main entrypoint
##

# parse args
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--provider', type=str, default='local')
parser.add_argument('--model', type=str, default=None)
parser.add_argument('--host', type=str, default='127.0.0.1')
parser.add_argument('--port', type=int, default=5000)
args = parser.parse_args()

# run server
app = LangTutor(provider=args.provider, model=args.model)
serve(host=args.host, port=args.port)
