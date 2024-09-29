import os
import shutil
import subprocess
import sys
from pathlib import Path

from PyQt5.QtCore import QDir, QModelIndex, QPoint, Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont, QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QFileSystemModel,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QTreeView,
)

from Editor import Editor


class FileManager(QTreeView):
    def __init__(self, tab_view, setNewTab=None, main_window=None) -> None:
        super(FileManager, self).__init__(None)

        self.setNewTab = setNewTab
        self.tab_view = tab_view
        self.main_window = main_window

        self.manager_font = QFont("Microsoft YaHei", 11)  # font size

        self.model: QFileSystemModel = QFileSystemModel()
        self.model.setRootPath(os.getcwd())

        # file system filter
        self.model.setFilter(
            QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files | QDir.Drives
        )
        self.model.setReadOnly(False)
        self.setFocusPolicy(Qt.NoFocus)

        self.setFont(self.manager_font)
        self.setModel(self.model)
        self.setRootIndex(self.model.index(os.getcwd()))
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # highlight the whole row whe selecting
        self.setSelectionBehavior(QTreeView.SelectRows)
        # User cannot edit file in tree view
        self.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)

        # add custom context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        # address mouse click
        self.clicked.connect(self.treeViewClicked)
        self.setIndentation(10)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # hide header and hide other columns except for name
        self.setHeaderHidden(True)
        self.setColumnHidden(1, True)
        self.setColumnHidden(2, True)
        self.setColumnHidden(3, True)

        # enabel drag and drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)

        self.previous_rename_name = None
        self.is_renaming = False
        self.current_edit_index = None

        self.itemDelegate().closeEditor.connect(self.onEditorClosed)

    def showContextMenu(self, pos: QPoint):
        idx = self.indexAt(pos)
        menu = QMenu(self)
        menu.addAction("New File")
        menu.addAction("New Folder")
        menu.addAction("Open in the Explorer")

        if idx.column() == 0:
            menu.addAction("Rename")
            menu.addAction("Delete")

        action = menu.exec(self.viewport().mapToGlobal(pos))
        if not action:
            return

        if action.text() == "New File":
            self.actionNewFile(idx)
        elif action.text() == "New Folder":
            self.actionNewFolder(idx)
        elif action.text() == "Rename":
            self.actionRename(idx)
        elif action.text() == "Delete":
            self.actionDelete(idx)
        elif action.text() == "Open in the Explorer":
            self.OpenInExplorer(idx)
        else:
            pass

    def OpenInExplorer(self, idx: QModelIndex):
        path = os.path.abspath(self.model.filePath(idx))
        is_dir = self.model.isDir(idx)
        if os.name == "nt":
            # Windows
            if is_dir:
                subprocess.Popen(f'explorer "{path}"')
            else:
                subprocess.Popen(f'explorer /select,"{path}"')
        elif os.name == "posix":
            # Linux or Mac OS
            if sys.platform == "darwin":
                # macOS
                if is_dir:
                    subprocess.Popen(["open", path])
                else:
                    subprocess.Popen(["open", "-R", path])
            else:
                # Linux
                subprocess.Popen(["xdg-open", os.path.dirname(path)])
        else:
            raise OSError(f"Unsupported platform {os.name}")

    def actionNewFile(self, idx: QModelIndex):
        root_path = self.model.rootPath()
        if idx.column() != -1 and self.model.isDir(idx):
            self.expand(idx)
            root_path = self.model.filePath(idx)

        f = Path(root_path) / "file"
        count = 1
        while f.exists():
            f = Path(f.parent / f"file{count}")
            count += 1
        f.touch()
        index = self.model.index(str(f.absolute()))
        self.edit(index)

    def actionNewFolder(self):
        f = Path(self.model.rootPath()) / "New Folder"
        count = 1
        while f.exists():
            f = Path(f.parent / f"New Folder{count}")
            count += 1
        idx = self.model.mkdir(self.rootIndex(), f.name)
        # edit that index
        self.edit(idx)

    def actionRename(self, idx: QModelIndex):
        self.edit(idx)
        self.previous_rename_name = self.model.fileName(idx)
        self.is_renaming = True
        self.current_edit_index = idx

    def deleteFile(self, path: Path):
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    def showDialog(self, title, msg) -> int:
        dialog = QMessageBox(self)
        dialog.setFont(self.manager_font)
        dialog.font().setPointSize(14)
        dialog.setWindowTitle(title)
        dialog.setWindowIcon(QIcon("./icons/close.png"))
        dialog.setText(msg)
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.No)
        dialog.setIcon(QMessageBox.Warning)
        return dialog.exec_()

    def actionDelete(self, idx: QModelIndex):
        # check if selection
        file_name = self.model.fileName(idx)
        dialog = self.showDialog(
            "Delete", f"Are you sure you want to delete {file_name}"
        )
        if dialog == QMessageBox.Yes:
            if self.selectionModel().selectedRows():
                for i in self.selectionModel().selectedRows():
                    path = Path(self.model.filePath(i))
                    self.deleteFile(path)
                    for editor in self.tab_view.findChildren(Editor):
                        if editor.path.name == path.name:
                            self.tab_view.removeTab(self.tab_view.indexOf(editor))

    def onEditorClosed(self):
        if self.is_renaming:
            self.renameFileWithIndex()

    def renameFileWithIndex(self):
        new_name = self.model.fileName(self.current_edit_index)
        if self.previous_rename_name == new_name:
            return

        # loop over all the tabs open and find the one with the old name
        for editor in self.tab_view.findChildren(
            Editor
        ):  # finding all children of type Editor
            if (
                editor.path.name == self.previous_rename_name
            ):  # the editor should keep a path vatriable
                editor.path = editor.path.parent / new_name
                self.tab_view.setTabText(self.tab_view.indexOf(editor), new_name)
                self.tab_view.repaint()
                editor.full_path = (
                    editor.path.absolute()
                )  # changing the editor instances full_path variable
                self.main_window.current_file = editor.path
                break

    def treeViewClicked(self, index: QModelIndex):
        path = self.model.filePath(index)
        p = Path(path)
        self.setNewTab(p)

    def dragEnterEvent(self, e: QDragEnterEvent | None) -> None:
        if e.mineData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e: QDropEvent) -> None:
        root_path = Path(self.model.rootPath())
        if e.mineData().hasUrls():
            for url in e.mimeData().urls():
                path = Path(url.toLocalFile())
                if path.is_dir():
                    shutil.copytree(path, root_path / path.name)
                else:
                    if root_path.samefile(self.model.rootPath()):
                        idx: QModelIndex = self.indexAt(e.pos())
                        if idx.column() == -1:
                            shutil.move(path, root_path / path.name)
                        else:
                            folder_path = Path(self.model.filePath(idx))
                            shutil.move(path, folder_path / path.name)
                    else:
                        shutil.copy(path, root_path / path.name)

        e.accept()
        return super().dropEvent(e)
