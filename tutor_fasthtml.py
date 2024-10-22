# fasthtml language tutor

import os
import uuid
import inspect
import uvicorn
import argparse
from collections import defaultdict

from starlette.responses import RedirectResponse
from fasthtml.common import *

from oneping.interface.fasthtml import ChatCSS, ChatJS, ChatWindow, websocket
from translate import LangChat, PROMPT_CHAT_PREFIX

##
## utilities
##

def gen_session_id():
    uid = str(uuid.uuid4())
    start, middle = uid[:4], uid[4:18]
    return f'{start}-{middle}'

def prune_injection(msg):
    role, content = msg['role'], msg['content']
    if role == 'user' and (match := re.search(PROMPT_CHAT_PREFIX, content)):
        pruned = content[match.end():].lstrip()
        return {'role': role, 'content': pruned}
    return msg

##
## components
##

def UrlInput(value=''):
    url = Input(
        id='url', cls='w-full p-2 font-mono text-sm outline-none bg-inherit',
        placeholder='Enter a URL', name='url', value=value
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

def LangTranslate(children=None):
    children = [
        FirstRow(), *[LangRow(orig, trans) for orig, trans in children], LastRow()
    ] if children is not None else []
    return Div(id='lang-pane', cls='w-full flex flex-col gap-2 p-2')(*children)

def LangHistory(history=None):
    history = [prune_injection(item) for item in history] if history is not None else []
    return ChatWindow(history=history, hx_vals='js:{...get_context()}')

def LangTutor(**kwargs):
    # make chat interface
    chats = defaultdict(lambda: LangChat(**kwargs))

    # create app object
    hdrs = [
        ScriptX('web/libs/fasthtml.js'),
        ScriptX('web/libs/htmx.min.js'),
        ScriptX('web/libs/ws.js'),
        ScriptX('web/libs/tailwind.min.js'),
        ScriptX('web/libs/marked.min.js'),
    ]
    app = FastHTML(hdrs=hdrs, default_hdrs=False)

    # assign session_id
    @app.get('/')
    def index():
        print('/index')
        session_id = gen_session_id()
        return RedirectResponse(f'/{session_id}')

    # get article
    @app.ws('/article')
    async def article(session_id: str, url: str, send):
        print(f'/article[{session_id}]: {url}')
        chat = chats[session_id]

        # clear contents
        await send(LangTranslate())
        await send(LangHistory())

        # send start message
        await send('LANGTUTOR_START')

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
        # this is dumb, but it works
        if orig == inspect._empty:
            orig = None
        if trans == inspect._empty:
            trans = None

        # print query stats
        print(f'/generate[{session_id[:6]}]')
        print(f'QUERY: {query}')
        print(f'ORIG: {orig}')
        print(f'TRANS: {trans}')

        # get chat session
        chat = chats[session_id]
        has_ctx = orig is not None and trans is not None
        ctx = (orig, trans) if has_ctx else None

        # stream response
        stream = chat.stream_query(query, ctx=ctx)
        await websocket(query, stream, send)
        print('\nDONE')

    # connect main
    @app.get('/{session_id}')
    def index(session_id: str):
        # get or create chat
        chat = chats[session_id]

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
        url = UrlInput(chat.path)
        trans = LangTranslate(chat.texts)
        hist = LangHistory(chat.history)

        # panes and body
        scroll = Div(id='lang-scroll', cls='h-full overflow-y-scroll')(trans)
        left = Div(cls='h-full w-[70%] flex flex-col border-r border-gray-300')(url, scroll)
        right = Div(cls='h-full w-[30%] overflow-y-scroll bg-gray-100')(hist)
        body = Body(cls='h-screen w-screen flex flex-row')(left, right)

        # return
        return (title, style_oneping, style, script_oneping, script, session), body

    # return
    return app

##
## main entrypoint
##

# parse args
parser = argparse.ArgumentParser()
parser.add_argument('--provider', type=str, default='local')
parser.add_argument('--model', type=str, default=None)
parser.add_argument('--prefill', default=True, action=argparse.BooleanOptionalAction)
parser.add_argument('--max-tokens', type=int, default=8192)
parser.add_argument('--cache-dir', type=str, default='cache')
parser.add_argument('--host', type=str, default='127.0.0.1')
parser.add_argument('--port', type=int, default=5000)
args = parser.parse_args()

# run server
app = LangTutor(
    provider=args.provider, model=args.model, prefill=args.prefill,
    max_tokens=args.max_tokens, cache_dir=args.cache_dir
)
serve(host=args.host, port=args.port)
