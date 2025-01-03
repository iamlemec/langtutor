import os
import re
import json
import urllib
import asyncio
from bs4 import BeautifulSoup, Comment

import oneping

##
## tools
##

def parse_json(json_str):
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None

def load_jsonl(path):
    with open(path, 'r') as fid:
        for line in fid:
            yield parse_json(line)

def save_jsonl(path, data):
    with open(path, 'w') as fid:
        for row in data:
            line = json.dumps(row, ensure_ascii=False)
            print(line, file=fid)

def url_hash(url):
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', url)
    return safe_name[:255]

def strip_text(text):
    text = re.sub(r'[\t\u00A0\u200B]+', ' ', text) # html whitespace
    text = re.sub(r'\r', '', text) # windows line endings
    text = re.sub(r' +', ' ', text) # multiple spaces
    text = re.sub(r'\n{3,}', '\n\n', text) # many newlines
    return text.strip()

def unescape_quotes(text):
    return re.sub(r'\\"', '"', text)

# assumes ["orig", "trans"] structure
def failsafe_parse(text):
    match = re.match(r'^ *\[ *\"(.*)\" *, *\"(.*)\" *\] *$', text)
    if match is not None:
        orig, trans = map(unescape_quotes, match.groups())
        return orig, trans
    return None

##
## translation tools
##

SYSTEM_TRANSLATE = """You are a helpful assistant that handles the translation of text from news articles in various languages into English. When given the text of an article in a non-English language, translate it into English on a sentence-by-sentence basis. Ignore non-text content such as ads, headers, and footers. Translate the entire article in one message, do not return partial translations.

Return the result as a JSONL file where each line is a [original, translated] pair. For example, if the original text is:

전국 4개 기초단체장을 뽑은 재·보궐 선거에서 이변은 없었습니다. 보수 강세 지역으로 분류되는 부산 금정구청장 선거에선 국민의힘 윤일현 후보가 당선됐습니다. 윤 후보는 조국혁신당과 야권 단일화에 성공한 민주당 김경지 후보를 20%p 넘는 차이로 꺾었습니다.

Then the returned JSONL line should be:

["전국 4개 기초단체장을 뽑은 재·보궐 선거에서 이변은 없었습니다.", "There were no surprises in the by-elections for four local government heads across the country."]
["보수 강세 지역으로 분류되는 부산 금정구청장 선거에선 국민의힘 윤일현 후보가 당선됐습니다.", "In the election for the Geumjeong-gu mayor in Busan, classified as a conservative stronghold, Yoon Il-hyun of the People Power Party was elected."]
["윤 후보는 조국혁신당과 야권 단일화에 성공한 민주당 김경지 후보를 20%p 넘는 차이로 꺾었습니다.", "Candidate Yoon defeated Democratic Party candidate Kim Kyung-ji, who had successfully unified with the Cho Kuk Innovation Party and the opposition, by a margin of over 20 percentage points."]

However, if the article is quoting someone, do not split the quoted text into multiple sentences. For example, if the original text is:

"Me llamaron en febrero y me preguntaron si quería ser directora. Claro, yo flipé. Estaba en un campeonato de España de pista y dije, ¡¿cómo?!", reconoce con risa nerviosa, aún incrédula. "Tengo el título desde hace dos años, pero no me lo había planteado nunca, la verdad. Entonces, me reuní con ellos y vi que no estaban aquí por moda, sino que querían fomentar el ciclismo femenino de verdad".

You can return this as two JSONL lines:

["\"Me llamaron en febrero y me preguntaron si quería ser directora. Claro, yo flipé. Estaba en un campeonato de España de pista y dije, ¡¿cómo?!\", reconoce con risa nerviosa, aún incrédula.", "\"They called me in February and asked me if I wanted to be a director. Of course, I was amazed. I was at a Spanish track championship and said, what?!\" she admits with a nervous laugh, still incredulous."]
["\"Tengo el título desde hace dos años, pero no me lo había planteado nunca, la verdad. Entonces, me reuní con ellos y vi que no estaban aquí por moda, sino que querían fomentar el ciclismo femenino de verdad\".", "\"I've had the qualification for two years, but I had never considered it, honestly. Then, I met with them and saw they weren't here because it was trendy, but because they really wanted to promote women's cycling.\""]

As you see above, in the case of quoted text, it is helpful to escape the quotation marks inside the original and translated strings. The examples given here were in Korean and Spanish, but you may receive text in any language."""

PROMPT_TRANSLATE = """Here is the article text you should translate:"""

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

async def extract_text(url):
    # fetch and extract
    print(f'Fetching text')
    proc = await asyncio.create_subprocess_exec(
        'node', '../readability/index.js', url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    # check for errors and get text
    if proc.returncode != 0:
        print(f'Error executing Node.js script: {stderr.decode()}')
        return
    return strip_text(stdout.decode())

def translate_text(text, prompt=PROMPT_TRANSLATE, system=SYSTEM_TRANSLATE, max_tokens=8192, prefill=True, **kwargs):
    stream = oneping.stream_async(
        f'{prompt}\n\n{text}',
        prefill='["' if prefill else None,
        max_tokens=max_tokens,
        system=system,
        **kwargs
    )
    return iter_lines_buffered(stream)

async def translate_url(url, cache_dir=None, **kwargs):
    print(f'TRANSLATE URL: {url}')

    # get cache path
    if cache_dir is not None:
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        cache_path = os.path.join(cache_dir, url_hash(url))
        if os.path.exists(cache_path):
            print(f'LOADING FROM CACHE: {cache_path}')
            for chunk in load_jsonl(cache_path):
                await asyncio.sleep(0.2)
                yield chunk
            return

    # fetch and extract
    print('Extracting text')
    if (text := await extract_text(url)) is None:
        print(f'Error extracting text')
        return

    # translate text
    print('Translating text')
    trans = []
    async for chunk in translate_text(text, **kwargs):
        print(f'CHUNK: {chunk}')
        data = failsafe_parse(chunk)
        if data is not None:
            trans.append(data)
            yield data

    # save to cache
    if cache_dir is not None:
        save_jsonl(cache_path, trans)

    print(f'DONE TRANSLATING')

##
## chat tools
##

SYSTEM_CHAT = """
You are a helpful and playful language assistant. You answer questions posed by the user in plain text or markdown when necessary for lists or emphasis. The user is currently looking at a side-by-side translation of a news article. Their primary goal is to learn about the language in which the article is written. Answer any questions they have about the text, the translation, or about the original language in which the article is written. Here is the full text and translation of the article provided on a sentence-by-sentence basis:

BEGIN TEXT

{text}

END TEXT

Additionally, each user message may be prefaced by the text of the sentence that the user is currently looking at.
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

PROMPT_CHAT_PREFIX = """Now answer the following query from the user:"""

PROMPT_CHAT = """
{context}

{prefix}

{query}
"""

class LangChat(oneping.Chat):
    def __init__(self, prefill=True, max_tokens=8192, cache_dir=None, **kwargs):
        super().__init__(**kwargs)
        self.chat_args = dict(
            prefill=prefill, max_tokens=max_tokens, cache_dir=cache_dir, **kwargs
        )
        self.texts = None

    async def set_article(self, path, **kwargs):
        # reset translation state
        self.texts = []

        # get or translate article
        async for chunk in translate_url(path, **self.chat_args):
            self.texts.append(chunk)
            yield chunk

        # make system prompt and clear chat history
        full_text = '\n\n'.join(f'{orig}\n{trans}' for orig, trans in self.texts)
        self.system = SYSTEM_CHAT.format(text=full_text)
        self.clear()

    async def stream_query(self, query, ctx=None):
        if self.texts is None:
            return

        # make context
        if ctx is not None:
            orig, trans = ctx
            context = PROMPT_CHAT_CONTEXT.format(orig=orig, trans=trans)
        else:
            context = PROMPT_CHAT_GLOBAL

        # stream response
        message = PROMPT_CHAT.format(context=context, prefix=PROMPT_CHAT_PREFIX, query=query)
        async for chunk in self.stream_async(message):
            oneping.sprint(chunk)
            yield chunk

##
## main
##

# translate article and save
async def main(path, provider='anthropic', native=False, cache=True, **kwargs):
    cache_dir = 'cache' if cache else None
    chunks = translate_url(url, provider=provider, native=native, cache_dir=cache_dir, **kwargs)
    async for orig, trans in chunks:
        data = json.dumps([orig, trans], ensure_ascii=False)
        print(data)

if __name__ == '__main__':
    import fire
    fire.Fire(main)
