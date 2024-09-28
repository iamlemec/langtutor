# fasthtml language tutor

import os
import uvicorn
from uvicorn.supervisors import ChangeReload
import fire

from fasthtml.common import *
from oneping.chat.fasthtml import chat_css, chat_js, ChatWindow, websocket

from translate import load_jsonl, save_jsonl, translate_url, stream_chat, make_chat

def LangRow(orig, trans):
    return Div(cls='w-full flex flex-col border p-2 gap-2')(
        Div(cls='w-full')(orig), Div(cls='w-full')(trans)
    )

def LangPane(texts):
    return Div(cls='w-full flex flex-col gap-2 p-2 overflow-y-scroll')(*[
        LangRow(orig, trans) for orig, trans in texts
    ])

def LangTutor(texts, chat):
    # create app object
    hdrs = [
        Script(src="https://cdn.tailwindcss.com"),
        Script(src='https://cdn.jsdelivr.net/npm/marked/marked.min.js')
    ]
    app = FastHTML(hdrs=hdrs, ws_hdr=True, debug=True, live=True)

    # connect main
    @app.route('/')
    def index():
        # chat style and script
        style, script = Style(chat_css), Script(chat_js)

        # window title
        title = Title('LangTutor')

        # lang and chat window
        lang = LangPane(texts)
        hist = ChatWindow(history=chat.history)

        # panes and body
        left = Div(cls='h-full w-[70%] overflow-y-scroll')(lang)
        right = Div(cls='h-full w-[30%] overflow-y-scroll')(hist)
        body = Body(cls='h-screen w-screen flex flex-row')(left, right)

        # return
        return (title, style, script), body

    # connect websocket
    @app.ws('/generate')
    async def generate(prompt: str, send):
        print(f'GENERATE: {prompt}')
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
