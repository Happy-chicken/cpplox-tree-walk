import os
import re
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QListWidgetItem


class SearchItem(QListWidgetItem):
    def __init__(self, name, full_path, lineno, end, line):
        self.name = name
        self.full_path = full_path
        self.lineno = lineno
        self.end = end
        self.line = line
        self.formated = f"{self.name}: {self.lineno}:{self.end}-{self.line}"
        super().__init__(self.formated)

    def __str__(self) -> str:
        return self.formated

    def __repr__(self) -> str:
        return self.formated


class SearchThread(QThread):
    """run search algorithm on this thread"""

    finished = pyqtSignal(list)

    def __init__(self) -> None:
        super(SearchThread, self).__init__(None)
        self.item = []
        self.search_path = ""
        self.search_text = ""
        self.search_project: bool = None

    def walkDir(self, path: str, exclude_dirs: list, exclude_files: list):
        for root, dirs, files in os.walk(path, topdown=True):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            files[:] = [
                f for f in files if f not in Path(f).suffixes not in exclude_files
            ]
            yield root, dirs, files

    @staticmethod
    def isBinary(path: Path) -> bool:
        with open(path, "rb") as f:
            return b"\0" in f.read(1024)

    def search(self):
        debug = False
        self.items = []
        exclude_dirs = [".git", ".vscode", ".venv", "__pycache__"]
        if self.search_project:
            exclude_dirs.append("venv")
        exclude_files = [".exe", ".svg", ".png", ".pyc"]
        for root, dirs, files in self.walkDir(
            self.search_path, exclude_dirs, exclude_files
        ):
            if len(self.items) > 5000:
                break
            for file in files:
                full_path = os.path.join(root, file)
                if self.isBinary(full_path):
                    break
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        try:
                            reg = re.compile(self.search_text, re.IGNORECASE)
                            for i, line in enumerate(f):
                                if m := reg.search(line):
                                    fd = SearchItem(
                                        file,
                                        full_path,
                                        i,
                                        m.end(),
                                        line[m.start() : m.end()].strip()[:50],
                                    )
                                    self.items.append(fd)
                        except re.error as e:
                            if debug:
                                print(f"{e}")
                except UnicodeDecodeError as e:
                    if debug:
                        print(f"{e}")
                    continue
        self.finished.emit(self.items)

    def run(self):
        self.search()

    def update(self, pattern, path, search_project):
        self.search_text = pattern
        self.search_path = path
        self.search_project = search_project
        self.start()
