import os
import re
import json
import requests
from bs4 import BeautifulSoup, Comment

from oneping import Chat

##
## tools
##

def parse_jsonl(jsonl):
    for line in jsonl.split('\n'):
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue

def load_jsonl(path):
    with open(path, 'r') as fid:
        return list(parse_jsonl(fid.read()))

def save_jsonl(path, texts):
    with open(path, 'w') as fid:
        for row in texts:
            print(json.dumps(row), file=fid)

def fetch_url(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

STRIP_TAGS = ['script', 'style', 'meta', 'link', 'noscript', 'nav', 'img', 'ol', 'ul']
def prune_html(html, strip_tags=STRIP_TAGS):
    # load html source
    soup = BeautifulSoup(html, 'html.parser')

    # filter out comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # filter out tags
    for tag in strip_tags:
        for source in soup.find_all(tag):
            source.decompose()

    # compress whitespace
    return re.sub(r'\n+', '\n', str(soup)).strip()

##
## translation tools
##

SYSTEM = 'You are a helpful assistant that handles html extraction and text translation from news articles in various languages.'

PROMPT_EXTRACT = 'Extract the article title and text from this html file. It is a news article that is likely in a non-English language. Return the result in plain text. Here is the html file:'

PROMPT_TRANSLATE = 'Translate this text into English on a sentence-by-sentence basis. Return the result as a JSONL file where each line is a [original, translated] pair. Here is the text:'

def extract_text(chat, html, prompt=PROMPT_EXTRACT, max_tokens=4096):
    return chat(
        f'{prompt}\n\n{html}',
        max_tokens=max_tokens
    )

def translate_text(chat, text, prompt=PROMPT_TRANSLATE, max_tokens=8192, prefill=True):
    return chat(
        f'{prompt}\n\n{text}',
        prefill='["' if prefill else None,
        max_tokens=max_tokens
    )

def translate_url(
    url, prompt_extract=PROMPT_EXTRACT, prompt_translate=PROMPT_TRANSLATE,
    provider='local', model=None, system=SYSTEM, max_tokens=4096, prefill=True
):
    chat = Chat(provider=provider, model=model, system=system)
    print(f'Fetching URL')
    html = fetch_url(url)
    prune = prune_html(html)
    print(f'Extracting text')
    text = extract_text(chat, prune, prompt=prompt_extract, max_tokens=max_tokens)
    print(f'Translating text')
    trans = translate_text(chat, text, prompt=prompt_translate, max_tokens=2*max_tokens, prefill=prefill)
    return list(parse_jsonl(trans))

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

MESSAGE_CHAT = """
The user is currently looking at the sentence:

ORIGINAL:

{orig}

TRANSLATION:

{trans}

Now answer the following query from the user:

{query}
"""

def translate_path(path, provider='local', model=None):
    # get file info
    fname = os.path.basename(path)
    fbase, fext = os.path.splitext(fname)

    # read file
    if fext == '.jsonl':
        texts = load_jsonl(path)
    else:
        texts = translate_url(path, provider=provider, model=model)

    # return texts
    return texts

class LangChat(Chat):
    def __init__(self, path=None, provider='local', model=None):
        super().__init__(provider=provider, model=model)
        if path is not None:
            self.set_article(path)

    def set_article(self, path):
        # get or translate article
        texts = translate_path(path, provider=self.provider, model=self.model)

        # make system prompt
        full_text = '\n\n'.join([f'{orig}\n{trans}' for orig, trans in texts])
        system = SYSTEM_CHAT.format(text=full_text)

        # store text and clear history
        self.texts = texts
        self.system = system
        self.clear()

    async def stream_query(self, orig, trans, query):
        message = MESSAGE_CHAT.format(orig=orig, trans=trans, query=query)
        async for chunk in self.stream_async(message):
            yield chunk

##
## main
##

# translate article and save
def main(path, save, provider='local', model=None):
    texts = translate_path(path, provider=provider, model=model)
    save_jsonl(save, texts)

if __name__ == '__main__':
    import fire
    fire.Fire(main)
