# fastapi language tutor

import json
import uvicorn
import argparse

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from translate import translate_url, LangChat, PROMPT_CHAT_PREFIX

##
## utilities
##

def prune_injection(msg):
    role, content = msg['role'], msg['content']
    if role == 'user' and (match := re.search(PROMPT_CHAT_PREFIX, content)):
        pruned = content[match.end():].lstrip()
        return {'role': role, 'content': pruned}
    return msg

def load_jsonl(path):
    with open(path) as fid:
        for line in fid:
            if len(text := line.strip()) > 0:
                yield json.loads(text)

##
## main interface
##

def main(host='127.0.0.1', port=5000, **kwargs):
    # make chat interface
    chats = LangChat(**kwargs)

    # make fastapi server
    app = FastAPI()

    # get article
    @app.post('/api/article')
    async def article(url: str):
        print(f'/article: {url}')
        # stream = translate_url(url)
        stream = load_jsonl('langtutor/cache/https___news_kbs_co_kr_news_pc_view_view_do_ncd_8140353')
        return StreamingResponse(stream, media_type='application/x-ndjson')

    # generate chat
    @app.post('/api/generate')
    async def generate(query: str, orig: str, trans: str):
        # print query stats
        print(f'/generate')
        print(f'QUERY: {query}')
        print(f'ORIG: {orig}')
        print(f'TRANS: {trans}')

        # get chat session
        has_ctx = orig is not None and trans is not None
        ctx = (orig, trans) if has_ctx else None

        # stream response
        stream = chat.stream_query(query, ctx=ctx)
        print('\nDONE')

    # run in uvicorn
    uvicorn.run(app, host=args.host, port=args.port)

##
## main entrypoint
##

# parse args
parser = argparse.ArgumentParser()
parser.add_argument('--provider', type=str, default='local')
parser.add_argument('--native', action='store_true')
parser.add_argument('--model', type=str, default=None)
parser.add_argument('--prefill', default=True, action=argparse.BooleanOptionalAction)
parser.add_argument('--max-tokens', type=int, default=8192)
parser.add_argument('--cache-dir', type=str, default='cache')
parser.add_argument('--host', type=str, default='127.0.0.1')
parser.add_argument('--port', type=int, default=5000)
args = parser.parse_args()

# run server
main(
    provider=args.provider, native=args.native, model=args.model, prefill=args.prefill,
    max_tokens=args.max_tokens, cache_dir=args.cache_dir
)
