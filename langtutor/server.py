# fastapi language tutor

import json
import uvicorn
import argparse

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

from .translate import translate_url, LangChat, PROMPT_CHAT_PREFIX

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

def main(host='127.0.0.1', port=5000, provider='anthropic', cache_dir='cache', **kwargs):
    # make chat interface
    chat = LangChat(cache_dir=cache_dir, provider=provider, **kwargs)

    # make fastapi server
    app = FastAPI()

    # get article
    @app.post('/api/article')
    async def article(request: Request):
        # get url
        data = await request.json()
        url = data['url']

        # print query stats
        print(f'/api/article')
        print(f'URL: {url}')

        # fetch article
        stream = (json.dumps(chunk) async for chunk in chat.set_article(url))
        return StreamingResponse(stream, media_type='application/x-ndjson')

    # generate chat
    @app.post('/api/generate')
    async def generate(request: Request):
        # get query
        data = await request.json()
        query = data['query']
        orig = data.get('orig', None)
        trans = data.get('trans', None)

        # print query stats
        print(f'/api/generate')
        print(f'QUERY: {query}')
        print(f'ORIG: {orig}')
        print(f'TRANS: {trans}')

        # get chat session
        has_ctx = orig is not None and trans is not None
        ctx = (orig, trans) if has_ctx else None

        # stream response
        stream = chat.stream_query(query, ctx=ctx)
        return StreamingResponse(stream, media_type='text/event-stream')

    # return app
    return app
