# text tools

import re
import json
from bs4 import BeautifulSoup, Comment
from textual.app import App
from textual.reactive import reactive
from textual.widgets import Input, Static
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

class BarePrompt(Input):
    def __init__(self, height, **kwargs):
        super().__init__(**kwargs)
        self.styles.border = ('none', None)
        self.styles.padding = (0, 1)
        self.styles.height = height

    def on_key(self, event):
        if event.key in ('up', 'down', 'pgup', 'pgdown'):
            event.prevent_default()

class UrlInput(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = 'url'
        self.styles.border = ('round', 'white')

    def compose(self):
        yield BarePrompt(id='prompt', height=1, placeholder='Enter an article URL...')

class LangPane(Static):
    position = reactive(0)

    def __init__(self, texts, **kwargs):
        super().__init__(**kwargs)
        self.styles.border_title = 'text'
        self.styles.border = ('round', 'white')
        self.texts = texts

    def watch_position(self):
        text = []
        for i, (orig, trans) in enumerate(self.texts):
            if i < self.position - 1:
                s = T(orig, 'bold') + '\n' + trans
            elif i == self.position - 1:
                s = T(orig, 'bold #ff0d57') + '\n' + T(trans, 'blue')
            else:
                s = orig
            text.append(s)
        self.update('\n\n'.join(text))

class LangScroll(VerticalScroll):
    def on_key(self, event):
        if event.key in ('up', 'down'):
            event.prevent_default()

##
## main app
##

class Tutor(App):
    CSS = """
    #prompt {
        background: $surface;
    }
    """

    BINDINGS = [
        ('u', 'up'  , 'Advance one sentence'),
        ('d', 'down', 'Go back one sentence'),
    ]

    def __init__(self, texts):
        super().__init__()
        self.styles.height = '1fr'
        self.texts = texts

    def compose(self):
        # yield UrlInput()
        yield LangScroll(LangPane(self.texts))

    def on_key(self, event):
        if event.key == 'up':
            self.action_up()
        elif event.key == 'down':
            self.action_down()

    def action_up(self):
        pane = self.query_one(LangPane)
        pane.position = max(0, pane.position - 1)

    def action_down(self):
        pane = self.query_one(LangPane)
        pane.position = min(len(pane.texts) + 1, pane.position + 1)

    # @work(thread=True)
    # async def pipe_stream(self, stream, setter):
    #     async for reply in cumcat(stream):
    #         self.call_from_thread(setter, reply)

def main(path):
    with open(path, 'r') as fid:
        texts = [json.loads(line) for line in fid.readlines()]
    app = Tutor(texts)
    app.run()

if __name__ == '__main__':
    import sys
    path = sys.argv[1]
    main(path)
