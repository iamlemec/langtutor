# text tools

import re
import json
from bs4 import BeautifulSoup, Comment
from textual.app import App
from textual.reactive import reactive
from textual.widgets import Static, Header
from textual.containers import VerticalScroll

##
## text tools
##

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

def T(t, c):
    return f'[{c}]{t}[/{c}]'

##
## widgets
##

class LangRow(Static):
    state = reactive(0)

    def __init__(self, orig, trans, **kwargs):
        super().__init__(**kwargs)
        self.styles.margin = (0, 0, 1, 0)
        self.orig = orig
        self.trans = trans

    def watch_state(self):
        if self.state == 0:
            self.update(T(self.orig, 'bold') + '\n' + self.trans)
        elif self.state == 1:
            self.update(T(self.orig, 'bold #ff0d57') + '\n' + T(self.trans, 'blue'))
        else:
            self.update(self.orig + '\n' + T(self.trans, 'gray15 on gray15'))

class LangPane(VerticalScroll, inherit_bindings=False):
    position = reactive(0)

    def __init__(self, texts, **kwargs):
        super().__init__(**kwargs)
        self.styles.margin = 1
        self.texts = texts

    def compose(self):
        for i, (orig, trans) in enumerate(self.texts):
            yield LangRow(orig, trans)

    def watch_position(self):
        for i, row in enumerate(self.query(LangRow)):
            if i < self.position - 1:
                row.state = 0
            elif i == self.position - 1:
                row.state = 1
                row.scroll_visible()
            else:
                row.state = 2

##
## main app
##

class Tutor(App):
    TITLE = 'LangTutor'

    CSS = """
    #prompt {
        background: $surface;
    }
    """

    BINDINGS = [
        ('up'      , 'up'      , 'Advance one sentence'),
        ('down'    , 'down'    , 'Go back one sentence'),
        ('pageup'  , 'pageup'  , 'Advance one page'    ),
        ('pagedown', 'pagedown', 'Go back one page'    ),
    ]

    def __init__(self, texts):
        super().__init__()
        self.styles.height = '1fr'
        self.texts = texts

    def compose(self):
        yield Header()
        yield LangPane(self.texts)

    def action_up(self):
        pane = self.query_one(LangPane)
        pane.position = max(0, pane.position - 1)

    def action_down(self):
        pane = self.query_one(LangPane)
        pane.position = min(len(pane.texts) + 1, pane.position + 1)

    def action_pageup(self):
        pane = self.query_one(LangPane)
        pane.scroll_page_up(force=True)

    def action_pagedown(self):
        pane = self.query_one(LangPane)
        pane.scroll_page_down(force=True)

##
## main entry
##

def main(path):
    with open(path, 'r') as fid:
        texts = [json.loads(line) for line in fid.readlines()]
    app = Tutor(texts)
    app.run()

if __name__ == '__main__':
    import sys
    path = sys.argv[1]
    main(path)
