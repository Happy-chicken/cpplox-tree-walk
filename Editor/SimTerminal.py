import subprocess

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QTextEdit


class TerminalThread(QThread):
    output_ready = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        process = subprocess.Popen(
            self.command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        while True:
            output = process.stdout.readline()
            if not output:
                break
            self.output_ready.emit(output.strip())


class TerminalWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            """
            background-color: #282c34;
            color: white;
            font-family: consolas; 
            font-size: 12pt;
            """
        )
        self.command_history = []
        self.setPlaceholderText("Enter commands here...")

    def keyPressEvent(self, event):
        if event.key() == 16777220:  # Enter key
            command = self.toPlainText().strip()
            if len(self.command_history) <= 20:
                self.command_history.append(command)
            else:
                self.command_history.clear()
                self.command_history.append(command)
            if command:
                print("commamnd->", command)
                self.clear()
                self.execute_command()
            else:
                self.append("System can't find file")

        else:
            super().keyPressEvent(event)

    def execute_command(self):
        command = self.command_history[-1]

        worker = TerminalThread(command)
        worker.output_ready.connect(lambda output: self.append(">> " + output + "\n"))
        worker.run()


# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()

#         self.setWindowTitle("Text Editor with Terminal")

#         # Create terminal-like widget
#         self.terminal_widget = TerminalWidget()

#         # Create layout and add terminal widget
#         layout = QVBoxLayout()
#         layout.addWidget(self.terminal_widget)

#         # Create central widget and set layout
#         central_widget = QWidget()
#         central_widget.setLayout(layout)
#         self.setCentralWidget(central_widget)


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     window.show()
#     sys.exit(app.exec_())
