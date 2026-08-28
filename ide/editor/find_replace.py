from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QLabel,
)

from ide import theme


class EditorArea(QWidget):
    """Контейнер редактора с наложенной панелью поиска."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._find_bar = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._area_layout = layout

    def addWidget(self, widget):
        self._area_layout.addWidget(widget, 1)

    def set_find_bar(self, bar):
        self._find_bar = bar
        bar.setParent(self)

    def show_find_bar(self):
        if self._find_bar is None:
            return

        self._find_bar.show()
        self._position_find_bar()

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if self._find_bar is not None and self._find_bar.isVisible():
            self._position_find_bar()

    def _position_find_bar(self):
        bar = self._find_bar

        # Опускаемся ниже панели вкладок, чтобы окно было внутри редактора,
        # а не поверх полосы табов.
        top = 35
        if self._area_layout.count():
            tabs = self._area_layout.itemAt(0).widget()
            if tabs is not None and hasattr(tabs, "tabBar"):
                h = tabs.tabBar().height()
                if h > 0:
                    top = h

        x = self.width() - bar.width() - 18
        y = top + 12

        bar.move(max(8, x), y)


class FindReplaceBar(QWidget):
    """
    VS Code-like Find / Replace widget для QScintilla.

    Структура:

        [⌄] [ Найти...              ][1/12][Aa][ab][↑][↓][×]
        [ ] [ Заменить...           ][⇄][≣]

    Replace-строка скрыта до раскрытия.
    """

    findRequested = pyqtSignal(bool)

    # Ширина рамки. Один источник правды: используется и в QSS, и в расчёте
    # высоты виджета, чтобы содержимое не перекрывало нижнюю границу.
    BORDER_WIDTH = 1

    def __init__(self, editor_provider, parent=None):
        super().__init__(parent)

        self._editor_provider = editor_provider

        self._active = False
        self._text = ""
        self._forward = True

        self.setObjectName("FindReplaceBar")
        self.setAttribute(Qt.WA_StyledBackground, True)

        # Размер близкий к VS Code.
        self.setFixedWidth(450)

        self._build_ui()
        self._apply_style()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        CONTROL_HEIGHT = 30
        INPUT_WIDTH = 200

        self._row_h = CONTROL_HEIGHT

        root = QHBoxLayout(self)
        root.setContentsMargins(
            self.BORDER_WIDTH,
            self.BORDER_WIDTH,
            self.BORDER_WIDTH,
            self.BORDER_WIDTH,
        )
        root.setSpacing(0)
        

        # ==============================================================
        # EXPAND BUTTON
        # ==============================================================

        self.expand_btn = self._button(
            text="⌄",
            object_name="FindExpand",
            tooltip="Показать замену",
            checkable=True,
        )

        self.expand_btn.setFixedSize(
            CONTROL_HEIGHT,
            CONTROL_HEIGHT,
        )

        self.expand_btn.toggled.connect(self._on_expand)

        root.addWidget(self.expand_btn)

        # ==============================================================
        # RIGHT SIDE
        # ==============================================================

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        # ==============================================================
        # FIND ROW
        # ==============================================================

        find_row = QHBoxLayout()
        find_row.setContentsMargins(0, 0, 0, 0)
        find_row.setSpacing(0)

        # --------------------------------------------------------------
        # Search input
        # --------------------------------------------------------------

        self.search = QLineEdit()
        self.search.setObjectName("FindInput")
        self.search.setPlaceholderText("Найти")
        self.search.setFixedSize(
            INPUT_WIDTH,
            CONTROL_HEIGHT,
        )
        self.search.setClearButtonEnabled(False)

        self.search.textChanged.connect(self._on_text_changed)
        self.search.returnPressed.connect(self.find_next)

        find_row.addWidget(self.search)

        # --------------------------------------------------------------
        # Match counter "x из x"
        # --------------------------------------------------------------

        self.count_label = QLabel("")
        self.count_label.setObjectName("FindCount")
        self.count_label.setFixedWidth(65)
        self.count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        find_row.addWidget(self.count_label)

        # --------------------------------------------------------------
        # Case
        # --------------------------------------------------------------

        self.case_btn = self._button(
            "Aa",
            "FindToggle",
            "Учитывать регистр",
            checkable=True,
        )

        self.case_btn.setFixedSize(
            CONTROL_HEIGHT,
            CONTROL_HEIGHT,
        )

        self.case_btn.toggled.connect(self._reset)

        find_row.addWidget(self.case_btn)

        # --------------------------------------------------------------
        # Whole word
        # --------------------------------------------------------------

        self.word_btn = self._button(
            "ab",
            "FindToggle",
            "Только целые слова",
            checkable=True,
        )

        self.word_btn.setFixedSize(
            CONTROL_HEIGHT,
            CONTROL_HEIGHT,
        )

        self.word_btn.toggled.connect(self._reset)

        find_row.addWidget(self.word_btn)

        # --------------------------------------------------------------
        # Previous
        # --------------------------------------------------------------

        self.up_btn = self._button(
            "↑",
            "FindAction",
            "Предыдущее совпадение",
        )

        self.up_btn.setFixedSize(
            CONTROL_HEIGHT,
            CONTROL_HEIGHT,
        )

        self.up_btn.clicked.connect(self.find_prev)

        find_row.addWidget(self.up_btn)

        # --------------------------------------------------------------
        # Next
        # --------------------------------------------------------------

        self.down_btn = self._button(
            "↓",
            "FindAction",
            "Следующее совпадение",
        )

        self.down_btn.setFixedSize(
            CONTROL_HEIGHT,
            CONTROL_HEIGHT,
        )

        self.down_btn.clicked.connect(self.find_next)

        find_row.addWidget(self.down_btn)

        # --------------------------------------------------------------
        # Close
        # --------------------------------------------------------------

        self.close_btn = self._button(
            "×",
            "FindClose",
            "Закрыть",
        )

        self.close_btn.setFixedSize(
            CONTROL_HEIGHT,
            CONTROL_HEIGHT,
        )

        self.close_btn.clicked.connect(self.hide_bar)

        find_row.addWidget(self.close_btn)

        right.addLayout(find_row)

        # ==============================================================
        # REPLACE ROW
        # ==============================================================

        self.replace_row = QWidget()
        self.replace_row.setObjectName("ReplaceRow")

        replace_layout = QHBoxLayout(self.replace_row)
        replace_layout.setContentsMargins(0, 0, 0, 0)
        replace_layout.setSpacing(0)
        replace_layout.setAlignment(Qt.AlignLeft)

        # --------------------------------------------------------------
        # Replace input
        # --------------------------------------------------------------

        self.replace = QLineEdit()
        self.replace.setObjectName("FindInput")
        self.replace.setPlaceholderText("Заменить")

        # ВАЖНО:
        # такая же ширина и высота, как у search.
        self.replace.setFixedSize(
            INPUT_WIDTH,
            CONTROL_HEIGHT,
        )

        self.replace.returnPressed.connect(self.replace_one)

        replace_layout.addWidget(self.replace)

        # --------------------------------------------------------------
        # Replace one
        # --------------------------------------------------------------

        self.replace_sel_btn = self._button(
            "⇄",
            "FindAction",
            "Заменить текущее совпадение",
        )

        self.replace_sel_btn.setFixedSize(
            CONTROL_HEIGHT,
            CONTROL_HEIGHT,
        )

        self.replace_sel_btn.clicked.connect(self.replace_one)

        replace_layout.addWidget(self.replace_sel_btn)

        # --------------------------------------------------------------
        # Replace all
        # --------------------------------------------------------------

        self.replace_all_btn = self._button(
            "≡",
            "FindAction",
            "Заменить все совпадения",
        )

        self.replace_all_btn.setFixedSize(
            CONTROL_HEIGHT,
            CONTROL_HEIGHT,
        )

        self.replace_all_btn.clicked.connect(self.replace_all)

        replace_layout.addWidget(self.replace_all_btn)

        right.addWidget(self.replace_row)

        root.addLayout(right)
        root.addStretch(1)

        self.search.installEventFilter(self)
        self.replace.installEventFilter(self)

        self.replace_row.setVisible(False)

        # Высота = содержимое + рамка с двух сторон, иначе виджеты
        # перекроют нижнюю границу.
        self.setFixedHeight(self._row_h + 2 * self.BORDER_WIDTH)


    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _button(
        self,
        text,
        object_name,
        tooltip,
        checkable=False,
    ):
        button = QToolButton()

        button.setText(text)
        button.setObjectName(object_name)
        button.setToolTip(tooltip)

        button.setCheckable(checkable)
        button.setAutoRaise(True)

        # Все кнопки одного размера.
        button.setFixedSize(26, 26)

        return button

    # ------------------------------------------------------------------
    # Style
    # ------------------------------------------------------------------

    def _apply_style(self):
        self.setStyleSheet(
            f"""
            QWidget#FindReplaceBar {{
                background-color: {theme.BG_ELEV};
                border: {self.BORDER_WIDTH}px solid {theme.BORDER};
                border-radius: 6px;
            }}

            QWidget#ReplaceRow {{
                background-color: {theme.BG_ELEV};
            }}

            QLabel#FindCount {{
                background-color: {theme.BG_ELEV};
                color: {theme.ACCENT};
                font-size: 18px;
                padding-left: 1px;
                padding-right: 1px;
            }}

            QLineEdit#FindInput {{
                background-color: {theme.BG};
                color: {theme.TEXT};
                border: 1px solid {theme.BG};
                border-radius: 3px;
                padding: 0 7px;
                selection-background-color: #473B2C;
            }}

            QLineEdit#FindInput:hover {{
                border: 1px solid {theme.BORDER};
            }}

            QLineEdit#FindInput:focus {{
                border: 1px solid {theme.ACCENT};
            }}

            QToolButton#FindExpand {{
                color: {theme.TEXT};
                background: transparent;
                border: none;
                padding: 0;
                border-radius: 3px;
                font-size: 22px;
            }}

            QToolButton#FindExpand:hover {{
                background-color: {theme.BORDER};
            }}



            QToolButton#FindToggle {{
                color: {theme.TEXT};
                background: transparent;
                border: none;
                padding: 0;
                border-radius: 3px;
                font-size: 17px;
                font-weight: 500;
            }}

            QToolButton#FindToggle:hover {{
                background-color: {theme.BORDER};
            }}

            QToolButton#FindToggle:checked {{
                color: {theme.ACCENT};
                background-color: {theme.BORDER};
            }}

            QToolButton#FindAction {{
                color: {theme.TEXT};
                background: transparent;
                border: none;
                padding: 0;
                border-radius: 3px;
                font-size: 21px;
            }}

            QToolButton#FindAction:hover {{
                background-color: {theme.BORDER};
                color: {theme.TEXT};
            }}

            QToolButton#FindAction:pressed {{
                background-color: {theme.BORDER};
            }}

            QToolButton#FindClose {{
                color: {theme.TEXT};
                background: transparent;
                border: none;
                padding: 0;
                border-radius: 3px;
                font-size: 24px;
            }}

            QToolButton#FindClose:hover {{
                background-color: {theme.BORDER};
                color: {theme.TEXT};
            }}
            """
        )

    # ------------------------------------------------------------------
    # Visibility
    # ------------------------------------------------------------------

    def show_for(self, editor=None, replace=False):
        host = self.parent()

        if host is not None and hasattr(host, "show_find_bar"):
            host.show_find_bar()
        else:
            self.show()

        if replace:
            self.expand_btn.setChecked(True)

        ed = self._editor_provider()

        if ed is not None and ed.hasSelectedText():
            selected = ed.selectedText()

            if "\n" not in selected:
                self.search.setText(selected)

        self.search.setFocus()
        self.search.selectAll()

        self._reset()

    def hide_bar(self):
        self._active = False

        ed = self._editor_provider()

        if ed is not None:
            ed.cancelFind()
            ed.setFocus()

        self.hide()

    # ------------------------------------------------------------------
    # Expand
    # ------------------------------------------------------------------

    def _on_expand(self, checked):
        self.replace_row.setVisible(checked)
        self.expand_btn.setText("⌃" if checked else "⌄")
        self.expand_btn.setFixedHeight((self._row_h * 2 if checked else self._row_h) + 6)
        self.setFixedHeight(
            (self._row_h * 2 if checked else self._row_h) + 6 * self.BORDER_WIDTH
        )

        host = self.parent()

        if host is not None and hasattr(host, "_position_find_bar"):
            host._position_find_bar()

    # ------------------------------------------------------------------
    # Keyboard
    # ------------------------------------------------------------------

    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress:
            if event.modifiers() & Qt.ControlModifier:
                if event.key() == Qt.Key_F:
                    self.findRequested.emit(False)
                    return True
                if event.key() == Qt.Key_H:
                    self.findRequested.emit(True)
                    return True

        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_F:
                self.findRequested.emit(False)
                event.accept()
                return
            if event.key() == Qt.Key_H:
                self.findRequested.emit(True)
                event.accept()
                return

        if event.key() == Qt.Key_Escape:
            self.hide_bar()
            event.accept()
            return

        if (
            event.key() in (Qt.Key_Return, Qt.Key_Enter)
            and event.modifiers() & Qt.ShiftModifier
        ):
            self.find_prev()
            event.accept()
            return

        super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Search state
    # ------------------------------------------------------------------

    def _cs(self):
        return self.case_btn.isChecked()

    def _wo(self):
        return self.word_btn.isChecked()

    def _reset(self):
        self._active = False
        self._text = ""

    def _on_text_changed(self, text):
        self._active = False
        self._text = ""

        ed = self._editor_provider()

        if ed is not None:
            ed.cancelFind()

        self._update_count()

    def _compute_count(self, ed, text, cs, wo):
        """Возвращает (всего_совпадений, текущий_индекс)."""
        import re

        src = ed.text()
        flags = 0 if cs else re.IGNORECASE

        if wo:
            pattern = r"(?<!\w)" + re.escape(text) + r"(?!\w)"
        else:
            pattern = re.escape(text)

        try:
            matches = list(re.finditer(pattern, src, flags))
        except re.error:
            return 0, 0

        total = len(matches)

        cur = 0
        if ed.hasSelectedText():
            sl, sc, _el, _ec = ed.getSelection()
            # QScintilla считает позиции в байтах (UTF-8), а re — в символах,
            # поэтому переводим начало каждого совпадения в байты.
            sel_off = ed.positionFromLineIndex(sl, sc)
            for m in matches:
                if len(src[:m.start()].encode("utf-8")) <= sel_off:
                    cur += 1

        return total, cur

    def _update_count(self):
        ed = self._editor_provider()
        text = self.search.text()

        if ed is None or not text:
            self.count_label.setText("")
            return

        total, cur = self._compute_count(ed, text, self._cs(), self._wo())

        if total == 0:
            self.count_label.setText("")
        else:
            self.count_label.setText(f"{cur} из {total}")

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def find_next(self):
        self._find(True)

    def find_prev(self):
        self._find(False)

    def _find(self, forward):
        ed = self._editor_provider()

        if ed is None:
            return

        text = self.search.text()

        if not text:
            return

        if (
            self._active
            and self._text == text
            and self._forward == forward
        ):
            ok = ed.findNext()

        else:
            line, col = ed.getCursorPosition()

            if forward and ed.hasSelectedText():
                sl, sc, el, ec = ed.getSelection()

                if (sl, sc) == (line, col):
                    line, col = el, ec

            ok = ed.findFirst(
                text,
                False,
                self._cs(),
                self._wo(),
                True,
                forward,
                line,
                col,
            )

        if ok:
            self._active = True
            self._text = text
            self._forward = forward
        else:
            self._active = False

        self._update_count()

    # ------------------------------------------------------------------
    # Replace
    # ------------------------------------------------------------------

    def replace_one(self):
        ed = self._editor_provider()

        if ed is None:
            return

        if not self._active:
            self._find(True)

        if ed.hasSelectedText():
            ed.replace(self.replace.text())
            self._find(True)

        self._update_count()

    def replace_all(self):
        ed = self._editor_provider()

        if ed is None:
            return

        text = self.search.text()

        if not text:
            return

        replacement = self.replace.text()

        ed.beginUndoAction()

        found = ed.findFirst(
            text,
            False,
            self._cs(),
            self._wo(),
            False,
            True,
            0,
            0,
        )

        count = 0

        while found:
            ed.replace(replacement)

            found = ed.findNext()

            count += 1

            if count > 100000:
                break

        ed.endUndoAction()

        self._active = False

        self._update_count()