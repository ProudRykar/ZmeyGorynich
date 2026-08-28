"""Виджет редактора .zg на базе QScintilla.

Обеспечивает: подсветку (ZGLexer), автодополнение (QsciAPIs),
подчёркивание ошибок (squiggle-индикатор) и маркеры в полях,
всплывающие подсказки (hover) и calltip'ы по сигнатурам функций.
"""
from PyQt5.Qsci import QsciScintilla, QsciAPIs
from PyQt5.QtCore import QEvent, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QFont
from PyQt5.QtWidgets import QToolTip

from ide.editor.scintilla_lexer import ZGLexer, STYLE_DEFAULT, _mono_font
from ide.analysis.completions import build_api_list, SNIPPETS
from ide.analysis.hover import describe


class ZGEditor(QsciScintilla):
    default_font_size = 11

    # запрос на открытие панели поиска/замены (Ctrl+F / Ctrl+H)
    findRequested = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = None
        self.diagnostics = []
        self.symbols = None

        self.setUtf8(True)
        self.setFont(_mono_font(self.default_font_size))
        self.setLexer(ZGLexer(self))

        # отступы и табуляция
        self.setTabWidth(4)
        self.setIndentationsUseTabs(False)
        self.setAutoIndent(True)
        self.setIndentationWidth(4)
        self.setBackspaceUnindents(True)
        self.setTabIndents(True)

        # внешний вид
        self.setPaper(QColor("#1B1B1F"))
        self.setColor(QColor("#E6E6E6"))
        self.setCaretForegroundColor(QColor("#FFFFFF"))
        # фон поля номеров строк — тот же, что у редактора, чтобы не было
        # визуально отдельной «панели» слева
        self.setMarginsBackgroundColor(QColor("#1B1B1F"))
        self.setMarginsForegroundColor(QColor("#9AA0A6"))
        self.setMarginBackgroundColor(0, QColor("#1B1B1F"))
        self.setMarginType(0, QsciScintilla.NumberMargin)
        self.setMarginWidth(0, "0000")
        self.setFolding(QsciScintilla.NoFoldStyle)

        # колонка номеров строк — обычный моноширинный шрифт редактора,
        # чтобы не наследовать кастомный UI-шрифт (SPSL) из QSS
        mf = _mono_font(self.default_font_size)
        self.SendScintilla(
            QsciScintilla.SCI_STYLESETFONT, QsciScintilla.STYLE_LINENUMBER,
            mf.family().encode())
        self.SendScintilla(
            QsciScintilla.SCI_STYLESETSIZE, QsciScintilla.STYLE_LINENUMBER,
            mf.pointSize())

        # горизонтальный скролл — только когда текст шире окна
        self.SendScintilla(QsciScintilla.SCI_SETSCROLLWIDTHTRACKING, 1)
        self.SendScintilla(QsciScintilla.SCI_SETSCROLLWIDTH, 1)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Scintilla не пересчитывает ширину прокрутки при удалении длинной
        # строки, поэтому сбрасываем минимум при каждом изменении текста
        self.textChanged.connect(self._reset_hscroll_width)

        # индикатор ошибок (волнистая линия)
        self._indicator = 0
        self.indicatorDefine(QsciScintilla.SquiggleIndicator, self._indicator)
        self.setIndicatorForegroundColor(QColor("#F44747"), self._indicator)

        # маркер строки с ошибкой (пока отключён)
        self._marker = -1

        # автодополнение
        self.setAutoCompletionSource(QsciScintilla.AcsAPIs)
        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionReplaceWord(True)
        # не принимать подсказку автоматически по пробелу/другим символам —
        # иначе многословные фразы («плывун малый точный») вставляют лишние пробелы
        self.setAutoCompletionFillups("")

        # call-tips (нативные, по сигнатурам из QsciAPIs)
        self.setCallTipsVisible(True)
        self.setCallTipsStyle(QsciScintilla.CallTipsNoContext)
        self.setCallTipsBackgroundColor(QColor("#232329"))
        self.setCallTipsForegroundColor(QColor("#E6E6E6"))
        self.setCallTipsHighlightColor(QColor("#9CDCFE"))

        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(400)
        self._hover_timer.timeout.connect(self._show_hover)

    # --- свойства ---
    def path(self):
        return self._path

    def set_path(self, path):
        self._path = path

    # --- настройки редактора ---
    def set_font_size(self, size):
        ZGEditor.default_font_size = size
        self.setFont(_mono_font(size))
        mf = _mono_font(size)
        self.SendScintilla(
            QsciScintilla.SCI_STYLESETFONT, QsciScintilla.STYLE_LINENUMBER,
            mf.family().encode())
        self.SendScintilla(
            QsciScintilla.SCI_STYLESETSIZE, QsciScintilla.STYLE_LINENUMBER,
            mf.pointSize())

    def set_line_numbers_visible(self, visible):
        self.setMarginWidth(0, "0000" if visible else 0)

    # --- диагностика ---
    def set_diagnostics(self, diags):
        self.diagnostics = diags
        self.clearIndicatorRange(0, 0, self.lines() - 1,
                                 self.lineLength(max(0, self.lines() - 1)),
                                 self._indicator)
        self.markerDeleteAll(self._marker)
        for d in diags:
            line0 = max(0, d.line - 1)
            col0 = max(0, d.col - 1)
            length = max(1, self._word_length_at(line0, col0))
            self.fillIndicatorRange(line0, col0, line0, col0 + length, self._indicator)

    def _reset_hscroll_width(self):
        # заставляем Scintilla пересчитать scrollWidth по самой длинной
        # оставшейся строке (убирает «залипшую» полосу после удаления)
        self.SendScintilla(QsciScintilla.SCI_SETSCROLLWIDTH, 1)

    def _word_length_at(self, line, col):
        text = self.text(line)
        end = col
        while end < len(text) and (text[end].isalnum() or text[end] in "_"):
            end += 1
        return end - col

    # --- автодополнение ---
    def update_completions(self, symbols):
        self.symbols = symbols
        api = QsciAPIs(self.lexer())
        for item in build_api_list(symbols):
            api.add(item)
        api.prepare()

    # --- горячие клавиши ---
    def keyPressEvent(self, e):
        if e.modifiers() & Qt.ControlModifier:
            if e.key() == Qt.Key_F:
                self.findRequested.emit(False)
                e.accept()
                return
            if e.key() == Qt.Key_H:
                self.findRequested.emit(True)
                e.accept()
                return
        super().keyPressEvent(e)

    # --- hover ---
    def event(self, e):
        if e.type() == QEvent.Type.ToolTip:
            pos = self.SendScintilla(QsciScintilla.SCI_POSITIONFROMPOINTCLOSE, e.x(), e.y())
            if pos >= 0:
                self._hover_pos = pos
                self._hover_timer.start()
            return True
        return super().event(e)

    def _show_hover(self):
        pos = getattr(self, "_hover_pos", -1)
        if pos < 0:
            return
        line, index = self.lineIndexFromPosition(pos)
        word = self.wordAtLineIndex(line, index).strip()
        if not word:
            QToolTip.hideText()
            return
        text = describe(word, self.symbols)
        if text:
            QToolTip.showText(QCursor.pos(), text, self)
        else:
            QToolTip.hideText()

    # --- сниппеты ---
    def insert_snippet(self, name):
        snippet = SNIPPETS.get(name)
        if snippet:
            self.insert(snippet)
