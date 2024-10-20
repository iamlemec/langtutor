# fasthtml language tutor

import os
import uuid
import inspect
import uvicorn
import argparse
from collections import defaultdict

from fasthtml.common import *
from oneping.interface.fasthtml import ChatCSS, ChatJS, ChatWindow, websocket
from translate import LangChat

##
## components
##

def UrlInput():
    url = Input(
        id='url', cls='w-full p-2 font-mono text-sm outline-none bg-inherit',
        placeholder='Enter a URL', name='url'
    )
    button = Button(
        cls='font-mono text-sm outline-none border-b border-gray-300 rounded bg-blue-500 text-white m-2 pt-1 pb-1 pl-2 pr-2',
        id='translate', type='submit'
    )('Translate')
    outer = Div(cls='flex flex-row relative bg-gray-100 border-b border-gray-300 box-border')(url, button)
    return Form(
        hx_ext='ws', hx_vals='js:{...get_url()}', ws_send=True, ws_connect='/article'
    )(outer)

def LangRow(orig, trans, cls=''):
    orig = Div(cls='lang-orig w-full pl-2 pr-2 border-r border-gray-300')(Span(orig))
    trans = Div(cls='lang-trans w-full pl-2 pr-2')(Span(trans))
    return Div(cls=f'lang-row w-full flex flex-row border rounded-sm pt-2 pb-2 {cls}')(orig, trans)

def FirstRow():
    return Div(id='row-first', cls='lang-row hidden active')

def LastRow():
    return Div(id='row-last', cls='lang-row hidden')

def LangPane(empty=False):
    children = [FirstRow(), LastRow()] if not empty else []
    return Div(id='lang-pane', cls='w-full flex flex-col gap-2 p-2')(*children)

def LangTutor(cache_dir='cache', **kwargs):
    # make chat interface
    chats = defaultdict(lambda: LangChat(cache_dir=cache_dir, **kwargs))

    # create app object
    hdrs = [
        Script(src="https://cdn.tailwindcss.com"),
        Script(src='https://cdn.jsdelivr.net/npm/marked/marked.min.js')
    ]
    app = FastHTML(hdrs=hdrs, exts='ws')

    # connect main
    @app.get('/')
    def index(sess):
        # set session chat
        print('/index')
        session_id = str(uuid.uuid4())

        # get oneping content
        script_oneping = ChatJS()
        style_oneping = ChatCSS()

        # chat style and script
        style = StyleX('web/tutor_fasthtml.css')
        script = ScriptX('web/tutor_fasthtml.js')
        session = Script(f'session_id = "{session_id}"')

        # window title
        title = Title('LangTutor')

        # lang and chat window
        lang = LangPane()
        url = UrlInput()
        hist = ChatWindow(hx_vals='js:{...get_context()}')
        trans = Div(id='trans', cls='h-full overflow-y-scroll')(lang)

        # panes and body
        left = Div(cls='h-full w-[70%] flex flex-col border-r border-gray-300')(url, trans)
        right = Div(cls='h-full w-[30%] overflow-y-scroll bg-gray-100')(hist)
        body = Body(cls='h-screen w-screen flex flex-row')(left, right)

        # return
        return (title, style_oneping, style, script_oneping, script, session), body

    # get article
    @app.ws('/article')
    async def article(session_id: str, url: str, send):
        print(f'/article[{session_id[:6]}]: {url}')
        chat = chats[session_id]

        # send start message
        await send('LANGTUTOR_START')

        # make pane
        await send(LangPane(empty=True))

        # make first row
        first = FirstRow()
        await send(Div(first, hx_swap_oob='beforeend', id='lang-pane'))

        # set article
        async for orig, trans in chat.set_article(url):
            row_box = LangRow(orig, trans)
            await send(Div(row_box, hx_swap_oob='beforeend', id='lang-pane'))

        # make last row
        last = LastRow()
        await send(Div(last, hx_swap_oob='beforeend', id='lang-pane'))

        # send done message
        await send('LANGTUTOR_DONE')

    # connect websocket
    @app.ws('/generate')
    async def generate(session_id: str, query: str, orig: str, trans: str, send):
        if orig == inspect._empty:
            orig = None
        if trans == inspect._empty:
            trans = None
        print(f'/generate[{session_id[:6]}]')
        print(f'QUERY: {query}')
        print(f'ORIG: {orig}')
        print(f'TRANS: {trans}')
        chat = chats[session_id]
        has_ctx = orig is not None and trans is not None
        ctx = (orig, trans) if has_ctx else None
        stream = chat.stream_query(query, ctx=ctx)
        await websocket(query, stream, send)
        print('\nDONE')

    # return
    return app

##
## main entrypoint
##

# parse args
parser = argparse.ArgumentParser()
parser.add_argument('--provider', type=str, default='local')
parser.add_argument('--cache_dir', type=str, default='cache')
parser.add_argument('--host', type=str, default='127.0.0.1')
parser.add_argument('--port', type=int, default=5000)
args = parser.parse_args()

# run server
app = LangTutor(provider=args.provider, cache_dir=args.cache_dir)
serve(host=args.host, port=args.port)
