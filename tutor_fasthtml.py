# fasthtml language tutor

import os
import uvicorn
from uvicorn.supervisors import ChangeReload
import fire

from fasthtml.common import *
from oneping.chat.fasthtml import chat_css, chat_js, ChatWindow, websocket

from translate import load_jsonl, save_jsonl, translate_url, stream_chat, make_chat

def PhantomRow(id, cls=''):
    return Div(id=id, cls=f'lang-row hidden {cls}')

def LangRow(orig, trans, cls=''):
    orig = Div(cls='lang-orig w-full')(Span(orig))
    trans = Div(cls='lang-trans w-full')(Span(trans))
    return Div(cls=f'lang-row w-full flex flex-col border rounded-sm p-2 gap-2 {cls}')(orig, trans)

def LangPane(texts):
    first = PhantomRow('first', cls='active')
    last = PhantomRow('last')
    return Div(cls='w-full flex flex-col gap-2 p-2 overflow-y-scroll border-r border-gray-300')(
        first, *[LangRow(orig, trans) for orig, trans in texts], last
    )

def LangTutor(texts, chat):
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
            next.scrollIntoView({behavior: 'smooth', block: 'nearest'});
            event.preventDefault();
        } else if (event.key === 'ArrowUp') {
            const active = document.querySelector('.lang-row.active');
            const prev = active.previousElementSibling;
            if (prev == null) {
                return;
            }
            active.classList.remove('active');
            prev.classList.add('active');
            prev.scrollIntoView({behavior: 'smooth', block: 'nearest'});
            event.preventDefault();
        }
    });
    """)

    style_cursor = Style("""
    .lang-row.active {
        border-color: rgb(96 165 250);
    }
    .lang-row.active ~ .lang-row > .lang-trans {
        border-radius: 0.25rem;
    }
    .lang-row.active ~ .lang-row > .lang-trans > span {
        color: #eaeaea;
        background-color: #eaeaea;
    }
    """)

    # connect main
    @app.route('/')
    def index():
        # chat style and script
        style, script = Style(chat_css), Script(chat_js)

        # window title
        title = Title('LangTutor')

        # lang and chat window
        lang = LangPane(texts)
        hist = ChatWindow(history=chat.history, hx_vals='js:{...get_cursor()}')

        # panes and body
        left = Div(cls='h-full w-[70%] overflow-y-scroll')(lang)
        right = Div(cls='h-full w-[30%] overflow-y-scroll bg-gray-100')(hist)
        body = Body(cls='h-screen w-screen flex flex-row')(left, right)

        # return
        return (title, style, style_cursor, script, script_cursor), body

    # connect websocket
    @app.ws('/generate')
    async def generate(prompt: str, orig: str, trans: str, send):
        print(f'GENERATE: {prompt}')
        print(f'ORIG: {orig}')
        print(f'TRANS: {trans}')
        stream = chat.stream_async(prompt)
        await websocket(prompt, stream, send)
        print('\nDONE')

    # return
    return app

def tutor(path, provider='local', model=None, prefill=True, save=None):
    # get file info
    fname = os.path.basename(path)
    fbase, fext = os.path.splitext(fname)

    # read file
    if fext == '.jsonl':
        texts = load_jsonl(path)
    else:
        texts = translate_url(path, provider=provider, model=model, prefill=prefill)

    # save file
    if save is not None:
        save_jsonl(save, texts)

    # make chat instance
    chat = make_chat(texts, provider=provider, model=model)

    # create app
    return LangTutor(texts, chat)

##
## main entrypoint
##

# parse args
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('path', type=str)
parser.add_argument('--provider', type=str, default='local')
parser.add_argument('--model', type=str, default=None)
parser.add_argument('--prefill', type=str, default=True)
parser.add_argument('--save', type=str, default=None)
parser.add_argument('--host', type=str, default='127.0.0.1')
parser.add_argument('--port', type=int, default=5000)
args = parser.parse_args()

# run server
app = tutor(args.path, provider=args.provider, model=args.model, prefill=args.prefill, save=args.save)
serve()
