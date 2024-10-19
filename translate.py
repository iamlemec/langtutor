import os
import re
import json
import urllib
import asyncio
from bs4 import BeautifulSoup, Comment

from oneping import Chat

##
## tools
##

def parse_json(json_str):
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None

def parse_jsonl(jsonl):
    for line in jsonl.split('\n'):
        yield parse_json(line)

def load_jsonl(path):
    with open(path, 'r') as fid:
        return list(parse_jsonl(fid.read()))

def save_jsonl(path, texts):
    with open(path, 'w') as fid:
        for row in texts:
            print(json.dumps(row), file=fid)

def url_hash(url):
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', url)
    return safe_name[:255]

def strip_text(text):
    text = re.sub(r'[\t\u00A0\u200B]+', ' ', text)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'[\n\r]+ ?', '\n', text)
    return text.strip()

##
## translation tools
##

SYSTEM_TRANSLATE = 'You are a helpful assistant that handles html extraction and text translation from news articles in various languages.'

PROMPT_TRANSLATE = 'Translate this text into English on a sentence-by-sentence basis. Ignore non-text content such as ads, headers, and footers. Return the result as a JSONL file where each line is a [original, translated] pair. Here is the text:'

async def iter_lines_buffered(inputs):
    buffer = ''
    async for chunk in inputs:
        buffer += chunk
        lines = buffer.split('\n')
        buffer = lines.pop()
        for line in lines:
            if len(line) > 0:
                yield line
    if len(buffer) > 0:
        yield buffer

def translate_text(chat, text, prompt=PROMPT_TRANSLATE, max_tokens=8192, prefill=True):
    stream = chat.stream_async(
        f'{prompt}\n\n{text}',
        prefill='["' if prefill else None,
        max_tokens=max_tokens
    )
    return iter_lines_buffered(stream)

async def translate_url(
    url, prompt=PROMPT_TRANSLATE, system=SYSTEM_TRANSLATE, max_tokens=8192, prefill=True,
    cache_dir=None, **kwargs
):
    # get cache path
    if cache_dir is not None:
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        cache_path = os.path.join(cache_dir, url_hash(url))
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as fid:
                for chunk in fid:
                    print(f'CACHE: {chunk}')
                    await asyncio.sleep(0.2)
                    yield parse_json(chunk)
            return

    # make translator chat
    chat = Chat(system=system, **kwargs)

    # fetch and extract
    print(f'Fetching text')
    proc = await asyncio.create_subprocess_exec(
        'node', 'readability/index.js', url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    # check for errors and get text
    if proc.returncode != 0:
        print(f'Error executing Node.js script: {stderr.decode()}')
        return
    text = strip_text(stdout.decode())

    # translate text
    print(f'Translating text')
    trans = ''
    async for chunk in translate_text(chat, text, prompt=prompt, max_tokens=max_tokens, prefill=prefill):
        print(f'CHUNK: {chunk}')
        data = parse_json(chunk)
        if data is not None:
            trans += f'{chunk}\n'
            yield data

    # save to cache
    if cache_dir is not None:
        with open(cache_path, 'w') as fid:
            fid.write(trans)

##
## chat tools
##

SYSTEM_CHAT = """
You are a helpful and playful language assistant. The user is currently looking at a side-by-side translation of a news article. Their primary goal is to learn about the language in which the article is written. Answer any questions they have about the text, the translation, or about the original language in which the article is written. Here is the full text and translation of the article provided on a sentence-by-sentence basis:

BEGIN TEXT

{text}

END TEXT

Additionally, each user message will be prefaced by the text of the sentence that the user is currently looking at.
"""

PROMPT_CHAT_CONTEXT = """
The user is currently looking at the sentence:

ORIGINAL:

{orig}

TRANSLATION:

{trans}
"""

PROMPT_CHAT_GLOBAL = """
The user is not currently looking at a specific sentence, so consider the entire article.
"""

PROMPT_CHAT = """
{context}

Now answer the following query from the user:

{query}
"""

async def translate_path(path, **kwargs):
    # get file info
    fname = os.path.basename(path)
    fbase, fext = os.path.splitext(fname)

    # read file
    if fext == '.jsonl':
        with open(path, 'r') as fid:
            for line in fid:
                await asyncio.sleep(0.5)
                yield parse_json(line)
    else:
        async for chunk in translate_url(path, **kwargs):
            yield chunk

class LangChat(Chat):
    def __init__(self, path=None, cache_dir=None, **kwargs):
        super().__init__(**kwargs)
        self.cache_dir = cache_dir
        if path is not None:
            self.set_article(path)

    async def set_article(self, path, **kwargs):
        # reset states
        self.clear()
        self.texts = []

        # get or translate article
        async for chunk in translate_path(
            path, provider=self.provider, model=self.model, cache_dir=self.cache_dir, **kwargs
        ):
            self.texts.append(chunk)
            yield chunk

        # make system prompt
        full_text = '\n\n'.join([f'{orig}\n{trans}' for orig, trans in self.texts])
        self.system = SYSTEM_CHAT.format(text=full_text)

    async def stream_query(self, query, ctx=None):
        if ctx is not None:
            orig, trans = ctx
            context = PROMPT_CHAT_CONTEXT.format(orig=orig, trans=trans)
        else:
            context = PROMPT_CHAT_GLOBAL
        message = PROMPT_CHAT.format(context=context, query=query)
        async for chunk in self.stream_async(message):
            yield chunk

##
## main
##

# translate article and save
def main(path, save, provider='local', **kwargs):
    texts = translate_path(path, provider=provider, **kwargs)
    save_jsonl(save, texts)

if __name__ == '__main__':
    import fire
    fire.Fire(main)
