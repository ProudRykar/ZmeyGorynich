"""QPlainTextEdit, ведущий себя как терминал: программа пишет в него вывод,
а когда запрашивает ввод (внемли), пользователь набирает прямо в ту же область.
Редактировать можно только строку, набираемую в данный момент; история вывода
защищена от правок."""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QPlainTextEdit


class TerminalView(QPlainTextEdit):
    inputSubmitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self._input_start = -1

    def begin_input(self):
        self.setReadOnly(False)
        self.moveCursor(QTextCursor.End)
        self._input_start = self.textCursor().position()
        self.setFocus()

    def end_input(self):
        self.setReadOnly(True)
        self._input_start = -1

    def keyPressEvent(self, event):
        if self.isReadOnly():
            super().keyPressEvent(event)
            return

        key = event.key()
        tc = self.textCursor()
        before_start = tc.position() < self._input_start

        if key in (Qt.Key_Return, Qt.Key_Enter):
            full = self.toPlainText()[self._input_start:]
            line = full.split("\n", 1)[0]
            self.inputSubmitted.emit(line)
            super().keyPressEvent(event)
            self._input_start = self.textCursor().position()
            return

        if before_start and (event.text() or key in (Qt.Key_Backspace, Qt.Key_Delete)):
            event.ignore()
            return

        super().keyPressEvent(event)

    def insertFromMimeData(self, source):
        if self.isReadOnly() or self.textCursor().position() < self._input_start:
            return
        super().insertFromMimeData(source)
