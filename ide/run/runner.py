"""Запуск программы .zg в отдельном потоке с захватом вывода и ввода."""
import io
import queue
import sys

from PyQt5.QtCore import QThread, pyqtSignal

from ide.lang_core import tokenize, parse, Context, evaluate
from ide.analysis.analyzer import strip_ansi


class _StreamWriter(io.TextIOBase):
    """Перехватывает запись в stdout/stderr и стримит в GUI по мере появления."""

    def __init__(self, emit):
        super().__init__()
        self._emit = emit

    def write(self, s):
        if s:
            self._emit(s)
        return len(s)

    def flush(self):
        return None

    def isatty(self):
        return False


class _GuiStdin(io.TextIOBase):
    """Ввод, читающий строки, которые подаёт GUI (поле ввода внизу)."""

    def __init__(self, q, runner):
        super().__init__()
        self._q = q
        self._runner = runner

    def readline(self, limit=-1):
        self._runner.inputNeeded.emit()
        data = self._q.get()
        if data is None:
            return ""
        return data

    def write(self, s):
        return len(s)

    def readable(self):
        return True

    def writable(self):
        return False

    def isatty(self):
        return False


class Runner(QThread):
    outputReady = pyqtSignal(str)
    finishedRun = pyqtSignal(int, str)
    inputNeeded = pyqtSignal()

    def __init__(self, code, path):
        super().__init__()
        self.code = code
        self.path = path
        self._in_queue = queue.Queue()
        self._stdin = _GuiStdin(self._in_queue, self)

    def feed_input(self, text):
        self._in_queue.put(text + "\n")

    def run(self):
        old_in, old_out, old_err = sys.stdin, sys.stdout, sys.stderr
        sys.stdin = self._stdin
        sys.stdout = _StreamWriter(self.outputReady.emit)
        sys.stderr = _StreamWriter(self.outputReady.emit)
        try:
            tokens = tokenize(self.code)
            ast = parse(tokens, self.code)
            ctx = Context()
            evaluate(ast, ctx, current_file=self.path)
            self.finishedRun.emit(0, "")
        except Exception as exc:  # noqa: BLE001
            msg = strip_ansi(str(exc)).strip()
            self.outputReady.emit(msg + "\n")
            self.finishedRun.emit(1, msg)
        finally:
            sys.stdin, sys.stdout, sys.stderr = old_in, old_out, old_err
