from pathlib import Path
from typing import TYPE_CHECKING

from PyQt5.Qsci import QsciAPIs, QsciScintilla
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from . import resouces
from .AutoCompleter import AutoCompleterThread
from .EditorLexer import LoxCustomLexer

if TYPE_CHECKING:
    from Editor.MainLoxWindow import MainWindow


class Editor(QsciScintilla):
    def __init__(
        self, main_window, parent=None, path: Path = None, is_Lox_file: bool = True
    ) -> None:
        super().__init__(parent)
        self.main_window: MainWindow = main_window
        self.current_file_changed: bool = False
        self.first_launch: bool = True

        self.path = path
        self.is_Lox_file = is_Lox_file
        self.full_path = self.path.absolute()

        self.cursorPositionChanged.connect(self._cursorPositionChanged)
        self.textChanged.connect(self._textChanged)

        # encode
        self.setUtf8(True)
        # instance
        self.window_font = QFont("Microsoft Yahei")
        self.window_font.setPointSize(11)
        self.setFont(self.window_font)
        # brace match
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        # indentation
        self.setIndentationGuides(True)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(False)
        self.setAutoIndent(True)

        # TODO: add autocomplete
        self.setAutoCompletionSource(QsciScintilla.AcsAll)
        self.setAutoCompletionThreshold(1)  # after one char, autocomplete will show
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionUseSingle(QsciScintilla.AcusNever)
        # TODO: add caret settings
        self.setCaretForegroundColor(QColor("#dedcdc"))
        self.setCaretLineVisible(True)
        self.setCaretWidth(2)
        self.setCaretLineBackgroundColor(QColor("#2c313c"))

        # EOl
        self.setEolMode(QsciScintilla.EolWindows)
        self.setEolVisibility(False)

        if self.is_Lox_file:
            # TODO: add lexer
            self.loxlexer = LoxCustomLexer(self)
            self.loxlexer.setDefaultFont(self.window_font)
            self.__api = QsciAPIs(self.loxlexer)
            # *custom!: add some custom functions and Qscitilla will handle it
            # self.api.add("fun")
            self.auto_completer = AutoCompleterThread(self.full_path, self.__api)
            self.auto_completer.finished.connect(self.loadAutoAutoComplete)
            self.setLexer(self.loxlexer)
        else:
            self.setPaper(QColor("#282c34"))
            self.setColor(QColor("#abb2bf"))

        # * set up line numbers
        self.setMarginType(0, QsciScintilla.NumberMargin)
        self.setMarginWidth(0, "000")
        self.setMarginsForegroundColor(QColor("#ff888888"))
        self.setMarginsBackgroundColor(QColor("#282c34"))
        self.setMarginsFont(self.window_font)

    @property
    def currentFileChanged(self):
        return self.current_file_changed

    @currentFileChanged.setter
    def currentFileChanged(self, value: bool):
        curr_index = self.main_window.tab_view.currentIndex()
        if value:
            self.main_window.tab_view.setTabText(curr_index, "*" + self.path.name)
            self.main_window.setWindowTitle(
                f"*{self.path.name} - {self.main_window.app_name}"
            )
        else:
            if self.main_window.tab_view.tabText(curr_index).startswith("*"):
                self.main_window.tab_view.setTabText(
                    curr_index, self.main_window.tab_view.tabText(curr_index)[1:]
                )
                self.main_window.setWindowTitle(self.main_window.windowTitle()[1:])

        self._current_file_changed = value

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Space:
            self.atuoCompleFromAll()
        else:
            return super(Editor, self).keyPressEvent(event)

    def _cursorPositionChanged(self, line: int, index: int):
        if self.is_Lox_file:
            self.auto_completer.getCompletions(line + 1, index, self.text())

    def _textChanged(self):
        if not self.currentFileChanged and not self.first_launch:
            self.currentFileChanged = True
        if self.first_launch:
            self.first_launch = False

    def loadAutoAutoComplete(self):
        pass
