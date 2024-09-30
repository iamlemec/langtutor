# textual language tutor

import os
from textual.app import App
from textual.reactive import reactive
from textual.widgets import Static, Header
from textual.containers import VerticalScroll, Horizontal, Vertical

from oneping.chat.textual import ChatWindow
from translate import LangChat

##
## widgets
##

def T(t, c):
    return f'[{c}]{t}[/{c}]'

class LangRow(Static):
    DEFAULT_CSS = """
    LangRow {
        margin: 0 0 1 0;
    }
    """

    state = reactive(0)
    dark = reactive(True)

    def __init__(self, orig, trans, **kwargs):
        super().__init__(**kwargs)
        self.orig = orig
        self.trans = trans

    def render(self):
        if self.state == 0:
            return T(self.orig, 'bold') + '\n' + self.trans
        elif self.state == 1:
            return T(self.orig, 'bold #ff0d57') + '\n' + T(self.trans, 'blue')
        else:
            block = 'gray15' if self.dark else 'gray89'
            return self.orig + '\n' + T(self.trans, f'{block} on {block}')

class LangPane(VerticalScroll, inherit_bindings=False):
    DEFAULT_CSS = """
    LangPane {
        margin: 1;
        scrollbar-size-vertical: 0;
    }
    """

    position = reactive(0)

    def __init__(self, texts, **kwargs):
        super().__init__(**kwargs)
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
## tutor app
##

class LangTutor(App):
    TITLE = 'LangTutor'

    BINDINGS = [
        ('up'      , 'up'      , 'Advance one sentence'),
        ('down'    , 'down'    , 'Go back one sentence'),
        ('pageup'  , 'pageup'  , 'Advance one page'    ),
        ('pagedown', 'pagedown', 'Go back one page'    ),
    ]

    CSS = """
    LangPane {
        width: 2fr;
        margin: 0;
        border: round white;
    }
    ChatWindow {
        width: 1fr;
    }
    ChatHistory {
        height: auto;
    }
    """

    def __init__(self, chat):
        super().__init__()
        self.chat = chat

    def compose(self):
        yield Header()
        yield Horizontal(
            LangPane(self.chat.texts),
            ChatWindow(self.stream),
        )

    def get_cursor(self):
        pane = self.query_one(LangPane)
        row = pane.children[pane.position - 1]
        return row.orig, row.trans

    async def stream(self, query):
        orig, trans = self.get_cursor()
        async for chunk in self.chat.stream_query(orig, trans, query):
            yield chunk

    def action_up(self):
        pane = self.query_one(LangPane)
        pane.position = max(0, pane.position - 1)

    def action_down(self):
        pane = self.query_one(LangPane)
        pane.position = min(len(pane.texts) + 1, pane.position + 1)

    def action_pageup(self):
        pane = self.query_one(LangPane)
        pane.scroll_page_up()

    def action_pagedown(self):
        pane = self.query_one(LangPane)
        pane.scroll_page_down()

    def watch_dark(self, dark):
        for row in self.query(LangRow):
            row.dark = dark
        super().watch_dark(dark)

##
## main entry
##

def tutor(path, provider='local', model=None, prefill=True, save=None):
    chat = LangChat(path=path, provider=provider, model=model)
    app = LangTutor(chat)
    app.run()

if __name__ == '__main__':
    import fire
    fire.Fire(tutor)
