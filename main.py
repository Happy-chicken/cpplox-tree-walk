import sys

from PyQt5.QtWidgets import QApplication

from Editor.MainLoxWindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    interpreter_dir = r"./build\bin\Debug"
    pylox_editor = MainWindow(interpreter_dir)
    sys.exit(app.exec_())
