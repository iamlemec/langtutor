# fastapi language tutor

import json
import uvicorn
import argparse

from fastapi import FastAPI, Request
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

def stream_jsonl(path):
    with open(path) as fid:
        for line in fid:
            if len(text := line.strip()) > 0:
                yield text + '\n'

##
## main interface
##

def main(host='127.0.0.1', port=5000, cache_dir='cache', provider='anthropic', **kwargs):
    # make chat interface
    chats = LangChat(provider=provider, **kwargs)

    # make fastapi server
    app = FastAPI()

    # get article
    @app.post('/api/article')
    async def article(request: Request):
        # get url
        url = await request.json()
        url = url['url']

        # fetch article
        stream = (
            json.dumps(chunk) async for chunk in
            translate_url(url, cache_dir=cache_dir, provider=provider)
        )
        return StreamingResponse(stream, media_type='application/x-ndjson')

    # generate chat
    @app.post('/api/generate')
    async def generate(request: Request):
        # get query
        query = await request.json()
        query = query['query']
        orig = query['orig']
        trans = query['trans']

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

    # return app
    return app

##
## main entrypoint
##

if __name__ == '__main__':
    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('--provider', type=str, default='anthropic')
    parser.add_argument('--native', action='store_true')
    parser.add_argument('--model', type=str, default=None)
    parser.add_argument('--prefill', default=True, action=argparse.BooleanOptionalAction)
    parser.add_argument('--max-tokens', type=int, default=8192)
    parser.add_argument('--cache-dir', type=str, default='cache')
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()

    # run server
    app = main(
        provider=args.provider, native=args.native, model=args.model, prefill=args.prefill,
        max_tokens=args.max_tokens, cache_dir=args.cache_dir
    )

    # run in uvicorn
    uvicorn.run(app, host=args.host, port=args.port)
