import re
from bs4 import BeautifulSoup, Comment

strip_tags = ['script', 'style', 'meta', 'link', 'noscript', 'nav', 'img', 'ol', 'ul']

def prune_html(path):
    # load html source
    with open(path, 'r') as fid:
        soup = BeautifulSoup(fid, 'html.parser')

    # filter out comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # filter out tags
    for tag in strip_tags:
        for source in soup.find_all(tag):
            source.decompose()

    # compress whitespace
    source = str(soup)
    return re.sub(r'\n+', '\n', source).strip()
