import re
import json
import requests
from bs4 import BeautifulSoup, Comment

from oneping import Chat

##
## constants
##

STRIP_TAGS = ['script', 'style', 'meta', 'link', 'noscript', 'nav', 'img', 'ol', 'ul']

SYSTEM = 'You are a helpful assistant that handles html extraction and text translation from news articles in various languages.'

PROMPT_EXTRACT = 'Extract the article title and text from this html file. It is a news article that is likely in a non-English language. Return the result in plain text. Here is the html file:'

PROMPT_TRANSLATE = 'Translate this text into English on a sentence-by-sentence basis. Return the result as a JSONL file where each line is a [original, translated] pair. Here is the text:'

##
## text tools
##

def fetch_url(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

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

def extract_text(chat, html, prompt=PROMPT_EXTRACT, max_tokens=4096):
    return chat(f'{prompt}\n\n{html}', max_tokens=max_tokens)

def translate_text(chat, text, prompt=PROMPT_TRANSLATE, max_tokens=8192):
    return chat(f'{prompt}\n\n{text}', prefill='["', max_tokens=max_tokens)

def parse_jsonl(jsonl):
    for line in jsonl.split('\n'):
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue

def translate_url(
    url, prompt_extract=PROMPT_EXTRACT, prompt_translate=PROMPT_TRANSLATE,
    provider='local', system=SYSTEM, max_tokens=4096
):
    chat = Chat(provider=provider, system=system)
    print(f'Fetching URL')
    html = fetch_url(url)
    prune = prune_html(html)
    print(f'Extracting text')
    text = extract_text(chat, prune, prompt=prompt_extract, max_tokens=max_tokens)
    print(f'Translating text')
    trans = translate_text(chat, text, prompt=prompt_translate, max_tokens=2*max_tokens)
    return list(parse_jsonl(trans))
