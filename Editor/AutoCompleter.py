from jedi import Script
from jedi.api import Completion
from PyQt5.Qsci import QsciAPIs
from PyQt5.QtCore import QThread


class AutoCompleterThread(QThread):
    def __init__(self, file_path, api) -> None:
        super(AutoCompleterThread, self).__init__(None)
        self.file_path = file_path
        self.script: Script = None
        self.api: QsciAPIs = api
        self.completions: list[Completion] = None

        self.line = 0
        self.index = 0
        self.text = ""

    def run(self):
        try:
            self.script = Script(self.text, path=self.file_path)
            self.completions = self.script.complete(self.line, self.index)
            self.loadAutoComplete(self.completions)
        except Exception as e:
            print(e)
        self.finished.emit()

    def loadAutoComplete(self, completions):
        self.api.clear()
        [self.api.add(completion.name) for completion in completions]
        self.api.prepare()

    def getCompletions(self, line, index, text: str):
        self.line = line
        self.index = index
        self.text = text
        self.start()
