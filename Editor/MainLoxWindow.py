import os
import subprocess
import sys
import webbrowser
from multiprocessing import Process
from pathlib import Path

from PyQt5.Qsci import QsciScintilla
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QCursor, QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .Editor import Editor
from .FileManager import FileManager
from .FuzzySearcher import SearchItem, SearchThread
from .SimTerminal import TerminalWidget


class MainWindow(QMainWindow):
    def __init__(self, interpreter_dir=""):
        super(MainWindow, self).__init__()
        self.interpreter_dir = interpreter_dir
        self.side_bar_color = "#282c34"
        self.current_file = None
        self.init_ui()
        self.current_side_bar = "folder-icon"

    def init_ui(self):
        self.app_name = "BuYi IDE"
        self.setWindowTitle(self.app_name)
        self.setWindowIcon(QIcon("./Editor/icons/NUIST.png"))
        self.resize(1300, 900)

        self.setStyleSheet(open(r"./Editor/css/style.qss", "r").read())

        # Set the font of the window
        self.window_font = QFont("Microsoft Yahei")
        self.window_font.setPointSize(11)
        # Set the font of the entire application
        self.setFont(self.window_font)
        self.setUpMenu()
        self.setUpToolbar()
        self.setUpBody()
        self.setUpStatusBar()
        self.show()

    def getEditor(self, path: Path = None, is_Lox_file=True) -> QsciScintilla:
        """get an editor to add it into a tab"""
        editor = Editor(main_window=self, path=path, is_Lox_file=is_Lox_file)
        return editor

    @staticmethod
    def isBinary(path: Path) -> bool:
        with open(path, "rb") as f:
            return b"\0" in f.read(1024)

    def setNewTab(self, path: Path, is_new_file=False):
        """set a new tab
        @param: path: path of the new tab
        @param: is_new_file
        """
        if path.is_dir():
            return
        if not is_new_file and self.isBinary(path):
            self.statusBar().showMessage("Can't open a binary file.", 2000)
            return

        editor = self.getEditor(path, path.suffix in {".pylox", ".py", ".cpplox"})

        if is_new_file:
            self.tab_view.addTab(editor, "Untitled")
            self.setWindowTitle(f"Untitled - {self.app_name}")
            self.statusBar().showMessage("New file created.", 2000)
            self.tab_view.setCurrentIndex(self.tab_view.count() - 1)
            self.current_file = None
            return

        # check if the file is open
        for i in range(self.tab_view.count()):
            if (
                self.tab_view.tabText(i) == path.name
                or self.tab_view.tabText(i) == "*" + path.name
            ):
                self.tab_view.setCurrentIndex(i)
                self.current_file = path
                return

        # create new tab
        self.tab_view.addTab(editor, path.name)
        try:
            editor.setText(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            self.statusBar().showMessage("Encode error.", 2000)
        self.setWindowTitle(f"{path.name} - {self.app_name}")
        self.current_file = path
        self.tab_view.setCurrentIndex(self.tab_view.count() - 1)
        self.tab_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.statusBar().showMessage(f"Opened {path.name}", 2000)

    def setUpToolbar(self):
        tool_bar = self.addToolBar("tool-bar")
        tool_bar.setMovable(False)
        tool_bar.setStyleSheet(f"""
                                background-color : {self.side_bar_color};
                                color: white;
                                margin: 0px;
                                """)
        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tool_bar.addWidget(spacer)

        run_action = tool_bar.addAction("Run")
        run_icon = QIcon("Run")
        run_icon.addPixmap(
            QPixmap("./Editor/icons/svg-icon/play.svg").scaled(QSize(25, 25)),
            QIcon.Normal,
            QIcon.Off,
        )
        # run_action.setAlignment(Qt.AlignmentFlag.AlignRight)
        run_action.setIcon(run_icon)
        run_action.triggered.connect(self.runCode)

    def setUpMenu(self):
        # top menu
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet(f"""
                                background-color : {self.side_bar_color};
                                color: white;
                                margin: 0px;
                                border: none;
                                """)
        file_menu = menu_bar.addMenu("File")

        # File
        new_file = file_menu.addAction("New File")
        new_file.setShortcut("Ctrl+N")
        new_file.triggered.connect(self.newFile)

        file_menu.addSeparator()
        open_file = file_menu.addAction("Open File")
        open_file.setShortcut("Ctrl+O")
        open_file.triggered.connect(self.openFile)

        open_folder = file_menu.addAction("Open Folder")
        open_folder.setShortcut("Ctrl+K")
        open_folder.triggered.connect(self.openFolder)

        file_menu.addSeparator()
        save_file = file_menu.addAction("Save File")
        save_file.setShortcut("Ctrl+S")
        save_file.triggered.connect(self.saveFile)

        save_as = file_menu.addAction("Save As")
        save_as.setShortcut("Ctrl+Shift+S")
        save_as.triggered.connect(self.saveAs)

        # Edit
        edit_menu = menu_bar.addMenu("Edit")

        copy_action = edit_menu.addAction("Copy")
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy)

        # TODO: add more action like paste, cut, undo and redo

        # TODO: Run
        run_menu = menu_bar.addMenu("Run")
        run_action = run_menu.addAction("Run without debugging")
        run_action.triggered.connect(self.runCode)

        help_menu = menu_bar.addMenu("Help")
        about_action = help_menu.addAction("About")
        doc_action = help_menu.addAction("Doc")
        about_action.triggered.connect(self.showAbout)
        doc_action.triggered.connect(self.showDoc)

    def getFrame(self):
        frame = QFrame()
        frame.setFrameShape(QFrame.NoFrame)
        frame.setFrameShadow(QFrame.Plain)
        frame.setContentsMargins(0, 0, 0, 0)
        frame.setStyleSheet("""
            QFrame {
                background-color: #21252b;
                border-radius: 1px;
                border: none;
                padding: 5px;
                color: #D3D3D3;                                
            }
            QFrame: hover {
                color: white;
            }
        """)
        return frame

    def setCursorPointer(self, event):
        self.setCursor(Qt.PointingHandCursor)

    def setCursorArrow(self, event):
        self.setCursor(Qt.ArrowCursor)

    def getSideBarLabel(self, path, name):
        label = QLabel()
        label.setPixmap(QPixmap(path).scaled(QSize(45, 45)))
        label.setAlignment(Qt.AlignmentFlag.AlignTop)
        label.setFont(self.window_font)
        label.mousePressEvent = lambda e: self.showHideTab(e, name)

        label.enterEvent = self.setCursorPointer
        label.leaveEvent = self.setCursorArrow
        return label

    def setUpStatusBar(self):
        # Create status bar
        stat = QStatusBar(self)
        stat.setStyleSheet("color: #D3D3D3;color: white")
        stat.showMessage("Ready", 3000)
        self.setStatusBar(stat)

    def setUpBody(self):
        body_frame = QFrame()
        body_frame.setFrameShape(QFrame.StyledPanel)
        body_frame.setFrameShadow(QFrame.Raised)
        body_frame.setLineWidth(0)
        body_frame.setMidLineWidth(0)
        body_frame.setContentsMargins(0, 0, 0, 0)
        body_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        body = QHBoxLayout()
        # Set the contents margins of the body to 0 on all sides
        body.setContentsMargins(0, 0, 0, 0)
        # Set the spacing of the body to 0
        body.setSpacing(0)
        body_frame.setLayout(body)

        # tab widgets to add editor to
        self.tab_view = QTabWidget()
        self.tab_view.setContentsMargins(0, 0, 0, 0)
        self.tab_view.setTabsClosable(True)
        self.tab_view.setMovable(True)
        self.tab_view.setDocumentMode(True)
        self.tab_view.tabCloseRequested.connect(self.closeTab)

        # * side bar
        self.side_bar = QFrame()
        self.side_bar.setFrameShape(QFrame.NoFrame)
        self.side_bar.setFrameShadow(QFrame.Plain)
        self.side_bar.setStyleSheet(f"""
            background-color: {self.side_bar_color};                            
        """)
        side_bar_layout = QVBoxLayout()
        side_bar_layout.setContentsMargins(5, 10, 5, 0)
        side_bar_layout.setSpacing(0)
        side_bar_layout.setAlignment(Qt.AlignTop | Qt.AlignCenter)

        # * setup labels
        folder_label = self.getSideBarLabel("./Editor/icons/folder.png", "folder-icon")
        side_bar_layout.addWidget(folder_label)
        search_label = self.getSideBarLabel("./Editor/icons/search.png", "search-icon")
        side_bar_layout.addWidget(search_label)
        setting_label = self.getSideBarLabel(
            "./Editor/icons/setting_.png", "setting-icon"
        )
        # Add a stretch to push the setting label to the top
        side_bar_layout.addStretch(1)
        side_bar_layout.addWidget(setting_label, alignment=Qt.AlignBottom)
        self.side_bar.setLayout(side_bar_layout)

        self.hsplit = QSplitter(Qt.Horizontal)  # to splite file manager and editor
        self.vsplit = QSplitter(Qt.Vertical)  # to splite editor and sim-termianl
        # * file manager
        self.file_manager_frame = self.getFrame()
        self.file_manager_frame.setMaximumWidth(400)
        self.file_manager_frame.setMinimumWidth(200)

        self.file_manager_layout = QVBoxLayout()
        self.file_manager_layout.setContentsMargins(0, 0, 0, 0)
        self.file_manager_layout.setSpacing(0)

        # *tree view
        self.file_manager = FileManager(
            tab_view=self.tab_view, setNewTab=self.setNewTab, main_window=self
        )

        # set up file manager
        self.file_manager_layout.addWidget(self.file_manager)
        self.file_manager_frame.setLayout(self.file_manager_layout)
        # *search view
        self.search_frame = self.getFrame()
        self.search_frame.setMaximumWidth(400)
        self.search_frame.setMinimumWidth(200)

        search_layout = QVBoxLayout()
        search_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        search_layout.setContentsMargins(0, 10, 0, 0)
        search_layout.setSpacing(0)

        # search box
        search_input = QLineEdit()
        search_input.setPlaceholderText("Search")
        search_input.setFont(self.window_font)
        search_input.setAlignment(Qt.AlignmentFlag.AlignTop)
        search_input.setStyleSheet("""
            QLineEdit {
                background-color: #21252b;
                border-radius: 5px;
                border: 1px solid #D3D3D3;
                padding: 5px;
                color: #D3D3D3;                  
            }
            QLineEdit: hover {
                color: white;
                                   
            }                      
        """)

        # * check box view
        self.search_box = QCheckBox("Search in modules")
        self.search_box.setFont(self.window_font)
        self.search_box.setStyleSheet("color: white;margin-bottom: 10px")

        self.search_worker = SearchThread()
        self.search_worker.finished.connect(self.searchFinished)
        search_input.textChanged.connect(
            lambda text: self.search_worker.update(
                text,
                self.file_manager.model.rootDirectory().absolutePath(),
                self.search_box.isChecked(),
            )
        )
        # * search list view
        self.search_list_view = QListWidget()
        self.search_list_view.setFont(QFont("Arial", 13))
        self.search_list_view.setStyleSheet("""
            QListWidget {
                background-color: #21252b;
                border-radius: 5px;
                border: 1px solid #D3D3D3;
                padding: 5px;
                color: #D3D3D3;  
            }
        """)
        self.search_list_view.itemClicked.connect(self.searchListViewClicked)

        # *setup layout
        # add search and file manager (layout) into the frame
        search_layout.addWidget(search_input)
        search_layout.addSpacerItem(
            QSpacerItem(5, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        )
        search_layout.addWidget(self.search_box)
        search_layout.addWidget(self.search_list_view)
        self.search_frame.setLayout(search_layout)

        # * set sim-terminal
        self.sim_terminal = TerminalWidget()
        self.sim_terminal.setMinimumHeight(100)
        self.sim_terminal.setMaximumHeight(300)
        # add tree view and tab view
        self.hsplit.addWidget(self.file_manager_frame)
        self.vsplit.addWidget(self.tab_view)
        self.vsplit.addWidget(self.sim_terminal)
        self.hsplit.addWidget(self.vsplit)

        # add all frames in body
        body.addWidget(self.side_bar)
        body.addWidget(self.hsplit)

        body_frame.setLayout(body)

        self.setCentralWidget(body_frame)

    def searchFinished(self, items):
        self.search_list_view.clear()
        for i in items:
            self.search_list_view.addItem(i)

    def searchListViewClicked(self, item: SearchItem):
        self.setNewTab(Path(item.full_path))
        editor = self.tab_view.currentWidget()
        editor.setCursorPosition(item.lineno, item.end)
        editor.setFocus()

    def showDialog(self, title, msg) -> int:
        dialog = QMessageBox(self)
        dialog.setFont(self.font())
        dialog.font().setPointSize(14)
        dialog.setWindowTitle(title)
        dialog.setWindowIcon(QIcon(":/icons/close-icon.svg"))
        dialog.setText(msg)
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.No)
        dialog.setIcon(QMessageBox.Warning)
        return dialog.exec_()

    def closeTab(self, index):
        editor: Editor = self.tab_view.currentWidget()
        # when current widget is settings, delete it and return
        if self.tab_view.tabText(self.tab_view.indexOf(editor)) == "Settings":
            self.tab_view.removeTab(index)
            return
        if editor.currentFileChanged:
            dialog = self.showDialog(
                "Close",
                f"Do you want to save the changes made to {self.current_file.name}?",
            )
            if dialog == QMessageBox.Yes:
                self.save_file()
        self.tab_view.removeTab(index)

    def showHideTab(self, event, type_):
        if type_ == "folder-icon":
            if self.file_manager_frame not in self.hsplit.children():
                self.hsplit.replaceWidget(0, self.file_manager_frame)
        elif type_ == "search-icon":
            if self.search_frame not in self.hsplit.children():
                self.hsplit.replaceWidget(0, self.search_frame)
        elif type_ == "setting-icon":
            self.showSettings()
            return

        if self.current_side_bar == type_:
            # frame = self.hsplit.children()[0]
            frame = self.hsplit.widget(0)
            if frame.isHidden():
                frame.show()
            else:
                frame.hide()
                self.current_side_bar = None
                return
        else:
            # frame = self.hsplit.children()[0]
            frame = self.hsplit.widget(0)
            frame.show()

        self.current_side_bar = type_

    def newFile(self):
        self.setNewTab(Path("untitled"), is_new_file=True)

    def saveFile(self):
        if self.current_file is None and self.tab_view.count() == 0:
            return
        if self.current_file is None and self.tab_view.count() > 0:
            self.saveAs()
        editor: Editor = self.tab_view.currentWidget()
        self.current_file.write_text(editor.text())
        self.statusBar().showMessage(f"Saved {self.current_file.name}", 2000)
        editor.currentFileChanged = False

    def saveAs(self):
        editor: Editor = self.tab_view.currentWidget()
        if editor is None:
            return

        file_path = QFileDialog.getSaveFileName(self, "Save File", os.getcwd())[0]
        if file_path == "":
            self.statusBar().showMessage("Save cancelled", 2000)
            return

        path = Path(file_path)
        path.write_text(editor.text())
        self.tab_view.setTabText(self.tab_view.currentIndex(), path.name)
        self.statusBar().showMessage(f"Saved {path.name}", 2000)
        self.current_file = path
        editor.currentFileChanged = False

    def openFile(self):
        ops = QFileDialog.Options()
        ops |= QFileDialog.DontUseNativeDialog
        new_file, _ = QFileDialog.getOpenFileName(
            self,
            "Pick a file",
            "",
            "All Files (*);;PyLox Files (*.pylox);;CppLox Files (*.cpplox)",
            options=ops,
        )
        if new_file == "":
            self.statusBar().showMessage("Open cancelled", 2000)
            return
        file = Path(new_file)
        self.setNewTab(file)

    def openFolder(self):
        ops = QFileDialog.Options()
        ops |= QFileDialog.DontUseNativeDialog

        new_folder = QFileDialog.getExistingDirectory(
            self, "Pick a folder", "", options=ops
        )
        if new_folder:
            self.file_manager.model.setRootPath(new_folder)
            self.file_manager.setRootIndex(self.file_manager.model.index(new_folder))
            self.statusBar().showMessage(f"Opened {new_folder}", 2000)

    def copy(self):
        editor = self.tab_view.currentWidget()
        if editor is not None:
            editor.copy()

    def showAbout(self):
        # webbrowser.open("https://github.com/wizmann/pylox-gui")
        about_text = "BuYi IDE version-1.0"
        # 创建一个对话框来显示帮助内容
        dialog = QMessageBox()
        dialog.setWindowTitle("About")
        dialog.setText(about_text)
        dialog.exec_()

    def showDoc(self):
        webbrowser.open("https://github.com")

    def setInterpreterPath(self):
        # print(self.interpreter_path_input.text())
        self.interpreter_dir = self.interpreter_path_input.text()
        self.statusBar().showMessage(
            f"Set interpreter path to {self.interpreter_dir}", 2000
        )

    def showSettingsWindow(self):
        settings_window = QWidget()
        settings_layout = QVBoxLayout()
        # -------------------------------------
        # add input
        # add input layout(Horizal) to add confirm button
        input_layout = QHBoxLayout()
        # set interpreter path confirm button
        confirm_button = QPushButton("Confirm")

        confirm_button.clicked.connect(self.setInterpreterPath)
        confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; /* Green */
                border: none;
                color: white;
                padding: 10px 24px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                font-family: Microsoft Yahei;
                margin: 4px 2px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049; /* Darker Green */
    }
""")
        self.interpreter_path_input = QLineEdit()
        self.interpreter_path_input.setPlaceholderText("Set Interpreter Path")
        self.interpreter_path_input.setFont(self.window_font)
        self.interpreter_path_input.setStyleSheet("""
            QLineEdit {
                background-color: #21252b;
                border-radius: 5px;
                border: 1px solid #D3D3D3;
                padding: 5px;
                color: #D3D3D3;                  
            }
            QLineEdit: hover {
                color: white;
                                   
            }                      
        """)
        input_layout.addWidget(self.interpreter_path_input)
        input_layout.addWidget(confirm_button)
        # -------------------------------------
        settings_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        settings_layout.addLayout(input_layout)
        settings_window.setLayout(settings_layout)

        self.tab_view.addTab(settings_window, "Settings")
        self.tab_view.setCurrentIndex(self.tab_view.count() - 1)
        self.tab_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.statusBar().showMessage("Settings", 2000)

    def showSettings(self):
        setting_menu = QMenu(self)
        setting_menu.setStyleSheet(f"""
                                background-color : {self.side_bar_color};
                                color: white;
                                margin: 0px;
                                border: none;
                                """)
        setting_menu.setTitle("Settings")
        setting_action = setting_menu.addAction("Settings")
        setting_action.triggered.connect(self.showSettingsWindow)
        setting_menu.exec_(QCursor.pos())

    def runCode(self):
        editor: Editor = self.tab_view.currentWidget()
        if editor is None:
            self.statusBar().showMessage("No file")
            return
        if editor.path.read_text() == "":
            self.statusBar().showMessage("No input")
            return
        # self.localTerminalRun(self.interpreter_dir, editor.path)
        p = Process(
            target=self.localTerminalRun,
            args=(f"cd {self.interpreter_dir} && main.exe {editor.path}",),
        )
        p.start()
        p.join()

    @staticmethod
    def localTerminalRun(command: str):
        subprocess.Popen(
            ["start", "cmd", "/k", command],
            shell=True,
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    interpreter_dir = (
        r"E:\code\C_C++\Compilers\cpplox-tree-walk-cmake-mvsc\build\bin\Debug"
    )
    pylox_editor = MainWindow(os.path.join(interpreter_dir, "main.exe"))
    sys.exit(app.exec_())
