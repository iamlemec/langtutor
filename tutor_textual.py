import os
import json
from textual.app import App
from textual.reactive import reactive
from textual.widgets import Static, Header
from textual.containers import VerticalScroll

from translate import parse_jsonl, translate_url

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
    # get file info
    fname = os.path.basename(path)
    fbase, fext = os.path.splitext(fname)

    # read file
    if fext == '.jsonl':
        with open(path, 'r') as fid:
            data = fid.read()
        texts = list(parse_jsonl(data))
    else:
        texts = translate_url(path, provider=provider, model=model, prefill=prefill)

    # save file
    if save is not None:
        with open(save, 'w') as fid:
            for row in texts:
                print(json.dumps(row), file=fid)

    # run app
    app = LangTutor(texts)
    app.run()

if __name__ == '__main__':
    import fire
    fire.Fire(tutor)
