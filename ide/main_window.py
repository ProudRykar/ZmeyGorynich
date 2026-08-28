"""Главное окно IDE ZmeyGorynich.

Безрамочное окно с кастомной шапкой, боковой панелью (проводник/символы),
тёмной темой и панелями вывода/проблем.
"""
import os

import sys
import tempfile
from PyQt5.QtCore import Qt, QTimer, QSize, QPointF, QSettings
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPixmap, QPolygonF
from PyQt5.QtWidgets import (
    QAction, QApplication, QFileDialog, QHBoxLayout, QLabel,
    QListWidget,
    QListWidgetItem,     QMenu, QMenuBar, QMessageBox, QPlainTextEdit,
    QSizeGrip, QSizePolicy, QSplitter, QStatusBar, QTabWidget, QToolBar,
    QToolButton, QVBoxLayout, QWidget,
)

from ide.analysis.analyzer import analyze, strip_ansi
from ide import theme
from ide.editor.zg_editor import ZGEditor
from ide.editor.find_replace import FindReplaceBar, EditorArea
from ide.git_panel import GitPanel
from ide.run.runner import Runner
from ide.sidebar import Sidebar
from ide.terminal_view import TerminalView

SAMPLE = """# Приветствие на Zmey Gorynich
молвить("Гой-еси ты Русь родная") гойда

сотвори возвысь(основа быти цело, степень быти цело) изречет плывун ухожу я в пляс
    возверни основа ** степень
закончили пляски

результат = возвысь(2, 3) гойда
молвить(результат) гойда
"""

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _tinted_icon(color, kind):
    pm = QPixmap(16, 16)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    if kind == "play":
        p.drawPolygon(QPolygonF([QPointF(3, 2), QPointF(3, 14), QPointF(14, 8)]))
    p.end()
    return QIcon(pm)


class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(35)
        self.setStyleSheet(
            f"background-color: {theme.TITLE_BG};"
            f"border-bottom: 1px solid {theme.BORDER};")
        self._drag = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 6, 0)
        layout.setSpacing(0)

        logo = QLabel("ЗМЕЙ ГОРЫНЫЧ")
        logo.setObjectName("TitleLabel")
        if theme.TITLE_FONT_FAMILY:
            logo.setFont(QFont(theme.TITLE_FONT_FAMILY, 18))
        layout.addWidget(logo)

        layout.addSpacing(14)

        menu_group = QWidget(self)
        menu_group.setAttribute(Qt.WA_StyledBackground, True)
        mg = QHBoxLayout(menu_group)
        mg.setContentsMargins(0, 0, 0, 0)
        mg.setSpacing(6)

        self._file_btn = QToolButton(menu_group)
        self._file_btn.setText("Файл")
        self._file_btn.setObjectName("TitleMenuButton")
        self._file_btn.setPopupMode(QToolButton.InstantPopup)
        self._file_btn.setAttribute(Qt.WA_StyledBackground, True)
        self._style_title_button(self._file_btn, 20, theme.TITLE_BTN_HOVER)
        mg.addWidget(self._file_btn)

        ref_btn = QToolButton(menu_group)
        ref_btn.setText("Справочник")
        ref_btn.setObjectName("TitleRefButton")
        ref_btn.setAttribute(Qt.WA_StyledBackground, True)
        self._style_title_button(ref_btn, 20, theme.TITLE_BTN_HOVER)
        self.ref_btn = ref_btn
        mg.addWidget(ref_btn)

        layout.addWidget(menu_group)
        layout.addStretch(1)

    def set_file_menu(self, menu):
        self._file_btn.setMenu(menu)

        self._add_button("—", self._min, "Свернуть")
        self._add_button("▢", self._max, "Развернуть")
        close = self._add_button("✕", self._close, "Закрыть")
        close.setObjectName("TitleClose")
        close.setStyleSheet(
            "QToolButton { background-color: " + theme.TITLE_BG + ";"
            "color: " + theme.BUTTON_COLOR + "; border: none;"
            "border-radius: 5px; font-size: 14px; }"
            "QToolButton:hover { background-color: #C0392B; color: #FFFFFF; }")

    def _add_button(self, text, slot, tip):
        btn = QToolButton(self)
        btn.setObjectName("TitleButton")
        btn.setText(text)
        btn.setToolTip(tip)
        btn.setFixedSize(30, 22)
        btn.clicked.connect(slot)
        self._style_title_button(btn, 14, theme.TITLE_BTN_HOVER)
        self.layout().addWidget(btn)
        return btn

    def _style_title_button(self, btn, font_size, hover_color):
        btn.setStyleSheet(
            f"QToolButton {{ background-color: {theme.TITLE_BG};"
            f"color: {theme.BUTTON_COLOR}; border: none;"
            f"border-radius: 5px; padding: 2px 8px; font-size: {font_size}px; }}"
            f"QToolButton:hover {{ background-color: {hover_color}; }}")
        return btn

    def _min(self):
        self.window().showMinimized()

    def _max(self):
        w = self.window()
        if w.isMaximized():
            w.showNormal()
        else:
            w.showMaximized()

    def _close(self):
        self.window().close()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            w = self.window()
            self._drag = e.globalPos() - w.geometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if self._drag is not None and e.buttons() & Qt.LeftButton:
            self.window().move(e.globalPos() - self._drag)
            e.accept()

    def mouseReleaseEvent(self, e):
        self._drag = None

    def mouseDoubleClickEvent(self, e):
        self._max()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMinimumSize(900, 600)
        self.resize(1200, 780)
        self._temp_files = []

        self._runner = None
        self._ref_dialog = None
        self._pending_editor = None
        self._analyze_timer = QTimer(self)
        self._analyze_timer.setSingleShot(True)
        self._analyze_timer.setInterval(300)
        self._analyze_timer.timeout.connect(self._run_pending_analysis)

        self._build_ui()
        self._settings = self._load_settings()
        self.new_file()
        self._apply_settings_to_editors(self._settings)

    # ---------- построение UI ----------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setObjectName("root")

        self.title_bar = TitleBar(self)
        self.title_bar.ref_btn.clicked.connect(self._open_reference)
        self.title_bar.set_file_menu(self._build_file_menu())
        root.addWidget(self.title_bar)

        # основная область: боковая панель + редактор/вывод
        self.sidebar = Sidebar(self)
        self.sidebar.fileActivated.connect(self.open_path)
        self.sidebar.symbolActivated.connect(self._goto_linecol)
        self.sidebar.openFolderRequested.connect(self.open_folder)
        self.sidebar.set_root(PROJECT_ROOT)
        self.sidebar.current_editor_provider = self.current_editor
        self.sidebar.settingsChanged.connect(self._apply_settings)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.tabBar().setElideMode(Qt.ElideRight)

        self._build_run_corner()

        editor_container = EditorArea()
        evbox = editor_container.layout()
        evbox.setContentsMargins(0, 0, 0, 0)
        evbox.setSpacing(0)
        evbox.addWidget(self.tabs, 1)

        # панель поиска/замены — наложение в правом верхнем углу редактора
        self.find_bar = FindReplaceBar(self.current_editor)
        self.find_bar.hide()
        self.find_bar.findRequested.connect(self._show_find)
        editor_container.set_find_bar(self.find_bar)

        self.output = TerminalView()
        self.output.setObjectName("TerminalView")
        self.output.setReadOnly(True)
        self.output.setFont(QFont("DejaVu Sans Mono", 11))
        self.output.setPlaceholderText(
            "Вывод программы появится здесь после запуска (▶ Запустить).")

        self.problems = QListWidget()
        self.problems.setObjectName("ProblemsList")
        self.problems.itemDoubleClicked.connect(self._goto_problem)

        self.bottom = QTabWidget()
        self.bottom.setObjectName("BottomTabs")
        self.bottom.addTab(self.problems, "Проблемы")
        self.bottom.addTab(self.output, "Вывод")
        self._output_tab = self.output

        self.git_panel = GitPanel(PROJECT_ROOT)
        self.git_panel.openFileRequested.connect(self.open_path)
        self.bottom.addTab(self.git_panel, "Git")
        self.bottom.currentChanged.connect(self._on_bottom_tab_changed)

        vsplit = QSplitter(Qt.Vertical)
        vsplit.addWidget(editor_container)
        vsplit.addWidget(self.bottom)
        vsplit.setStretchFactor(0, 4)
        vsplit.setStretchFactor(1, 1)

        main = QSplitter(Qt.Horizontal)
        main.addWidget(self.sidebar)
        main.addWidget(vsplit)
        main.setStretchFactor(0, 0)
        main.setStretchFactor(1, 1)
        main.setSizes([260, 900])
        root.addWidget(main, 1)

        self._build_statusbar()
        root.addWidget(self.status_bar)

    # ---------- настройки IDE ----------
    def _load_settings(self):
        qs = QSettings("ZmeyGorynich", "IDE")
        size = qs.value("editor/font_size", ZGEditor.default_font_size, type=int)
        show_ln = qs.value("editor/show_line_numbers", True, type=bool)
        ZGEditor.default_font_size = size
        self.sidebar.font_spin.setValue(size)
        self.sidebar.ln_check.setChecked(show_ln)
        return {"font_size": size, "show_line_numbers": show_ln}

    def _apply_settings(self, settings):
        self._settings = settings
        ZGEditor.default_font_size = settings["font_size"]
        self._apply_settings_to_editors(settings)
        qs = QSettings("ZmeyGorynich", "IDE")
        qs.setValue("editor/font_size", settings["font_size"])
        qs.setValue("editor/show_line_numbers", settings["show_line_numbers"])

    def _apply_settings_to_editors(self, settings):
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i)
            if isinstance(ed, ZGEditor):
                ed.set_font_size(settings["font_size"])
                ed.set_line_numbers_visible(settings["show_line_numbers"])

    def _build_file_menu(self):
        file_menu = QMenu("Файл", self)
        new_a = QAction("Новый", self)
        new_a.triggered.connect(self.new_file)
        open_a = QAction("Открыть…", self)
        open_a.triggered.connect(self.open_file)
        save_a = QAction("Сохранить", self)
        save_a.triggered.connect(self.save_file)
        folder_a = QAction("Открыть папку…", self)
        folder_a.triggered.connect(self.open_folder)
        file_menu.addAction(new_a)
        file_menu.addAction(open_a)
        file_menu.addAction(folder_a)
        file_menu.addAction(save_a)
        file_menu.addSeparator()
        quit_a = QAction("Выход", self)
        quit_a.triggered.connect(self.close)
        file_menu.addAction(quit_a)
        return file_menu

    def _build_run_corner(self):
        # кнопки запуска/остановки — прямо на строке вкладок (правый угол)
        corner = QWidget()
        cl = QHBoxLayout(corner)
        cl.setContentsMargins(4, 0, 6, 0)
        cl.setSpacing(2)

        self._run_btn = QToolButton()
        self._run_btn.setObjectName("RunButton")
        self._run_btn.setText("Запустить ▶")
        self._run_btn.setStyleSheet(
            "QToolButton { color: #E6B450; background: transparent; "
            "border: 1px solid #5A4126; border-radius: 2px; "
            "padding: 2px 8px; font-size: 20px; } "
            "QToolButton:hover { background-color: rgba(230,180,80,0.18); }")
        self._run_btn.clicked.connect(self.run_current)
        cl.addWidget(self._run_btn)

        self._stop_btn = QToolButton()
        self._stop_btn.setObjectName("StopButton")
        self._stop_btn.setText("■")
        self._stop_btn.setFixedSize(30, 30)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self.stop_run)
        cl.addWidget(self._stop_btn)

        self.tabs.setCornerWidget(corner, Qt.TopRightCorner)

    def _build_statusbar(self):
        self.status_bar = QStatusBar()
        self.status_accent = QToolButton()
        self.status_accent.setObjectName("StatusAccent")
        self.status_accent.setText("")
        self.status_accent.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.status_accent.setCursor(Qt.PointingHandCursor)
        self.status_accent.clicked.connect(self._show_problems)
        self.status_text = QLabel("Готово")
        self.status_text.setObjectName("StatusText")
        self.status_bar.addWidget(self.status_accent)
        self.status_bar.addWidget(self.status_text, 1)
        self.status_bar.addPermanentWidget(QSizeGrip(self))

    # ---------- боковая панель ----------
    def _show_problems(self):
        self.bottom.setCurrentWidget(self.problems)

    # ---------- работа с вкладками ----------
    def _create_editor(self, path=None, content=""):
        editor = ZGEditor()
        editor.setObjectName("Editor")
        editor.setText(content)
        editor.set_path(path)
        editor.textChanged.connect(lambda: self._on_editor_changed(editor))
        editor.modificationChanged.connect(
            lambda modified: self._update_tab_title(editor, modified))
        editor.findRequested.connect(self._show_find)
        idx = self.tabs.addTab(editor, self._tab_title(editor))
        self.tabs.setCurrentIndex(idx)
        return editor

    def _tab_title(self, editor):
        path = editor.path()
        if not path:
            return "Безымянный.zg"
        return os.path.basename(path)

    def _show_find(self, replace=False):
        bar = self.find_bar

        if not bar.isVisible():
            bar.show_for(replace=replace)
            return

        if replace:
            if bar.expand_btn.isChecked():
                bar.hide_bar()
            else:
                bar.expand_btn.setChecked(True)
        else:
            bar.hide_bar()

    def _update_tab_title(self, editor, modified):
        idx = self.tabs.indexOf(editor)
        if idx < 0:
            return
        title = self._tab_title(editor)
        if modified:
            title += " •"
        self.tabs.setTabText(idx, title)

    def current_editor(self):
        return self.tabs.currentWidget()

    def new_file(self):
        editor = self._create_editor(path=None, content=SAMPLE)
        self._analyze(editor)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть .zg", PROJECT_ROOT,
            "ZmeyGorynich (*.zg);;Все файлы (*)")
        if path:
            self.open_path(path)

    def open_folder(self):
        path = QFileDialog.getExistingDirectory(
            self, "Открыть папку", PROJECT_ROOT)
        if path:
            self.sidebar.set_root(path)
            self.git_panel.set_repo_start(path)

    def _open_reference(self):
        from ide.reference import ReferenceDialog
        if self._ref_dialog is None:
            self._ref_dialog = ReferenceDialog(self)
        self._ref_dialog.show()
        self._ref_dialog.raise_()
        self._ref_dialog.activateWindow()

    def open_path(self, path):
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i)
            if ed.path() == path:
                self.tabs.setCurrentIndex(i)
                return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return
        editor = self._create_editor(path=path, content=content)
        editor.setModified(False)
        self._analyze(editor)

    def save_file(self):
        editor = self.current_editor()
        if editor is None:
            return
        path = editor.path()
        if not path:
            return self.save_file_as()
        self._write_file(editor, path)

    def save_file_as(self):
        editor = self.current_editor()
        if editor is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как .zg", "program.zg", "ZmeyGorynich (*.zg)")
        if not path:
            return
        if not path.endswith(".zg"):
            path += ".zg"
        self._write_file(editor, path)
        editor.set_path(path)
        self.sidebar.set_root(path)
        self._update_tab_title(editor, editor.isModified())

    def _write_file(self, editor, path):
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(editor.text())
            editor.setModified(False)
        except OSError as e:
            QMessageBox.critical(self, "Ошибка записи", str(e))

    def close_tab(self, index):
        editor = self.tabs.widget(index)
        if editor is not None and editor.isModified():
            ans = QMessageBox.question(
                self, "Сохранить?",
                f"Файл «{self.tabs.tabText(index)}» изменён. Сохранить?")
            if ans == QMessageBox.Yes:
                self.tabs.setCurrentIndex(index)
                self.save_file()
        self.tabs.removeTab(index)

    def _on_tab_changed(self, index):
        editor = self.tabs.widget(index)
        if editor is not None:
            self._refresh_problems(editor)

    def _on_bottom_tab_changed(self, index):
        if self.bottom.widget(index) is self.git_panel:
            self.git_panel.refresh()

    # ---------- анализ ----------
    def _on_editor_changed(self, editor):
        self._pending_editor = editor
        self._analyze_timer.start()

    def _run_pending_analysis(self):
        editor = self._pending_editor
        if editor is not None:
            self._analyze(editor)

    def _analyze(self, editor):
        code = editor.text()
        diags, symbols, _ast = analyze(code)
        editor.set_diagnostics(diags)
        editor.update_completions(symbols)
        if editor is self.current_editor():
            self.sidebar.set_symbols(symbols)
            self._refresh_problems(editor)
        self._update_status(diags)

    def _refresh_problems(self, editor):
        self.problems.clear()
        for d in editor.diagnostics:
            kind = "Ошибка" if d.severity == "error" else "Предупреждение"
            item = QListWidgetItem(f"{d.line}:{d.col}  [{kind}]  {d.message}")
            item.setData(Qt.UserRole, (d.line, d.col))
            self.problems.addItem(item)
        if self.problems.count() == 0:
            self.problems.addItem("(проблем не найдено)")

    def _goto_problem(self, item):
        data = item.data(Qt.UserRole)
        if not data:
            return
        self._goto_linecol(data)

    def _goto_linecol(self, data):
        line, col = data
        editor = self.current_editor()
        if editor is not None:
            editor.setCursorPosition(line - 1, max(0, col - 1))
            editor.ensureLineVisible(line - 1)
            editor.setFocus()

    def _update_status(self, diags=None):
        if diags is None:
            editor = self.current_editor()
            diags = editor.diagnostics if editor else []
        errs = sum(1 for d in diags if d.severity == "error")
        warns = sum(1 for d in diags if d.severity == "warning")
        self.status_text.setText("Готово")
        self.status_accent.setText(f"⚠ {warns}   ✕ {errs}")

    # ---------- запуск ----------
    def run_current(self):
        editor = self.current_editor()
        if editor is None:
            return
        code = editor.text()
        path = editor.path()
        if not path:
            fd, path = tempfile.mkstemp(suffix=".zg")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(code)
            self._temp_files.append(path)

        self.output.setPlainText("")
        self.output.end_input()
        self.bottom.setCurrentWidget(self._output_tab)

        self._orig_std = (sys.stdin, sys.stdout, sys.stderr)
        self._runner = Runner(code, path)
        self._runner.outputReady.connect(self._append_output)
        self._runner.finishedRun.connect(self._on_run_finished)
        self._runner.inputNeeded.connect(self._on_input_needed)
        self.output.inputSubmitted.connect(self._on_input_submitted)
        self._run_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self.status_text.setText("Выполнение...")
        self._runner.start()

    def _append_output(self, text):
        self.output.insertPlainText(strip_ansi(text))
        sb = self.output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_input_needed(self):
        self.bottom.setCurrentWidget(self._output_tab)
        self.output.begin_input()

    def _on_input_submitted(self, text):
        if self._runner is not None and self._runner.isRunning():
            self._runner.feed_input(text)

    def _on_run_finished(self, code, msg):
        if self._orig_std is not None:
            sys.stdin, sys.stdout, sys.stderr = self._orig_std
            self._orig_std = None
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self.output.end_input()
        if code == 0:
            self.status_text.setText("Выполнено успешно")
        else:
            self.status_text.setText("Ошибка выполнения")
            self.bottom.setCurrentWidget(self._output_tab)

    def stop_run(self):
        if self._runner is not None and self._runner.isRunning():
            self._runner.terminate()
            if self._orig_std is not None:
                sys.stdin, sys.stdout, sys.stderr = self._orig_std
                self._orig_std = None
            self.status_text.setText("Остановлено")
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self.output.end_input()

    def closeEvent(self, event):
        for p in self._temp_files:
            try:
                os.remove(p)
            except OSError:
                pass
        super().closeEvent(event)
