"""Панель управления git (source control) в стиле VS Code.

Показывает текущую ветку, список изменённых файлов с возможностью
поотдельного индексирования (чекбокс = файл проиндексирован), поле
сообщения коммита, а также кнопки commit / push / pull / refresh.

Все операции делегируются модулю :mod:`ide.git_backend`, который
вызывает системный git через subprocess.
"""
import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ide import theme
from ide.git_backend import GitRepo, GitError


_STAGED_COLOR = QColor("#73C991")
_MODIFIED_COLOR = QColor("#E6B450")
_UNTRACKED_COLOR = QColor("#9AA0A6")


class GitPanel(QWidget):
    openFileRequested = pyqtSignal(str)

    def __init__(self, repo_start, parent=None):
        super().__init__(parent)

        self._repo = GitRepo.discover(repo_start)
        self._refreshing = False

        self._build_ui()
        self._apply_style()
        self.refresh()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # --- верхняя панель: ветка + действия ---
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(6)

        self.branch_label = QLabel("—")
        self.branch_label.setObjectName("GitBranch")
        top.addWidget(self.branch_label)
        top.addStretch(1)

        self.refresh_btn = self._tool("↻", "Обновить")
        self.refresh_btn.clicked.connect(self.refresh)
        self.stage_all_btn = self._tool("+", "Проиндексировать всё")
        self.stage_all_btn.clicked.connect(self._stage_all)
        self.unstage_all_btn = self._tool("−", "Убрать всё из индекса")
        self.unstage_all_btn.clicked.connect(self._unstage_all)
        self.commit_btn = self._tool("⎇", "Закоммитить")
        self.commit_btn.clicked.connect(self._commit)
        self.push_btn = self._tool("⇡", "Отправить (push)")
        self.push_btn.clicked.connect(self._push)
        self.pull_btn = self._tool("⇣", "Забрать (pull)")
        self.pull_btn.clicked.connect(self._pull)

        for b in (self.refresh_btn, self.stage_all_btn, self.unstage_all_btn,
                  self.commit_btn, self.push_btn, self.pull_btn):
            top.addWidget(b)

        root.addLayout(top)

        # --- сообщение коммита ---
        self.commit_edit = QPlainTextEdit()
        self.commit_edit.setObjectName("GitCommit")
        self.commit_edit.setPlaceholderText("Сообщение коммита…")
        self.commit_edit.setMaximumHeight(56)
        root.addWidget(self.commit_edit)

        # --- список файлов ---
        self.list = QListWidget()
        self.list.setObjectName("GitList")
        self.list.itemChanged.connect(self._on_item_changed)
        self.list.itemDoubleClicked.connect(self._on_item_double)
        root.addWidget(self.list, 1)

        # --- строка состояния ---
        self.status_label = QLabel("")
        self.status_label.setObjectName("GitStatus")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        self._update_controls()

    def _tool(self, text, tooltip):
        btn = QToolButton()
        btn.setText(text)
        btn.setToolTip(tooltip)
        btn.setObjectName("GitTool")
        return btn

    def _apply_style(self):
        self.setStyleSheet(
            f"""
            QLabel#GitBranch {{
                color: {theme.ACCENT};
                font-size: 13px;
                font-weight: 600;
                padding-right: 6px;
            }}
            QToolButton#GitTool {{
                background-color: {theme.BG_PANEL};
                color: {theme.TEXT};
                border: 1px solid {theme.BORDER};
                border-radius: 6px;
                padding: 3px 9px;
                font-size: 14px;
            }}
            QToolButton#GitTool:hover {{
                background-color: {theme.BG_ELEV};
                border: 1px solid {theme.ACCENT};
            }}
            QPlainTextEdit#GitCommit {{
                background-color: {theme.BG_PANEL};
                border: 1px solid {theme.BORDER};
                border-radius: 6px;
                color: {theme.TEXT};
                padding: 4px 6px;
                font-size: 13px;
            }}
            QPlainTextEdit#GitCommit:focus {{ border: 1px solid {theme.ACCENT}; }}
            QListWidget#GitList {{
                background-color: {theme.BG_PANEL};
                border: 1px solid {theme.BORDER};
                border-radius: 6px;
                color: {theme.TEXT};
            }}
            QLabel#GitStatus {{
                color: {theme.TEXT_DIM};
                font-size: 12px;
                padding: 2px 4px;
            }}
            """
        )

    # ------------------------------------------------------------------
    # Публичное API
    # ------------------------------------------------------------------

    def set_repo_start(self, path):
        self._repo = GitRepo.discover(path)
        self.refresh()

    def refresh(self):
        if self._repo is None:
            self.branch_label.setText("не git-репозиторий")
            self.list.clear()
            self._set_status("Откройте папку внутри git-репозитория.", error=True)
            self._update_controls()
            return

        self._refreshing = True
        try:
            self.branch_label.setText(self._repo.branch())
            files = self._repo.status()
        except GitError as exc:
            self._refreshing = False
            self._set_status(str(exc), error=True)
            self._update_controls()
            return

        self.list.clear()
        for f in files:
            item = QListWidgetItem()
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if f["staged"] else Qt.Unchecked)
            item.setData(Qt.UserRole, f["path"])
            item.setText(self._item_text(f))
            item.setForeground(self._item_color(f))
            self.list.addItem(item)

        self._refreshing = False
        self._set_status("")
        self._update_controls()

    # ------------------------------------------------------------------
    # Обработчики
    # ------------------------------------------------------------------

    def _on_item_changed(self, item):
        if self._refreshing or self._repo is None:
            return

        path = item.data(Qt.UserRole)
        try:
            if item.checkState() == Qt.Checked:
                self._repo.stage(path)
            else:
                self._repo.unstage(path)
        except GitError as exc:
            self._set_status(str(exc), error=True)
        self.refresh()

    def _on_item_double(self, item):
        if self._repo is None:
            return
        path = item.data(Qt.UserRole)
        full = os.path.join(self._repo.root, path)
        if os.path.exists(full):
            self.openFileRequested.emit(full)

    def _stage_all(self):
        if self._repo is None:
            return
        try:
            self._repo.stage_all()
            self._set_status("Все изменения проиндексированы.")
        except GitError as exc:
            self._set_status(str(exc), error=True)
        self.refresh()

    def _unstage_all(self):
        if self._repo is None:
            return
        try:
            self._repo.unstage_all()
            self._set_status("Индекс очищен.")
        except GitError as exc:
            self._set_status(str(exc), error=True)
        self.refresh()

    def _commit(self):
        if self._repo is None:
            return
        message = self.commit_edit.toPlainText().strip()
        if not message:
            self._set_status("Введите сообщение коммита.", error=True)
            return
        try:
            out = self._repo.commit(message)
        except GitError as exc:
            self._set_status(str(exc), error=True)
            return
        self.commit_edit.clear()
        self._set_status(out or "Коммит выполнен.")
        self.refresh()

    def _push(self):
        if self._repo is None:
            return
        out = self._repo.push()
        self._set_status(out or "Push выполнен.", error=("error" in out.lower()
                         or "fatal" in out.lower()))
        self.refresh()

    def _pull(self):
        if self._repo is None:
            return
        out = self._repo.pull()
        self._set_status(out or "Pull выполнен.", error=("error" in out.lower()
                         or "fatal" in out.lower()))
        self.refresh()

    # ------------------------------------------------------------------
    # Утилиты отображения
    # ------------------------------------------------------------------

    @staticmethod
    def _item_text(f):
        letter = f["x"] if f["x"] != " " else f["y"]
        if f["rename"]:
            return f"{letter}  {f['rename']} → {f['path']}"
        return f"{letter}  {f['path']}"

    @staticmethod
    def _item_color(f):
        if f["untracked"]:
            return _UNTRACKED_COLOR
        if f["staged"]:
            return _STAGED_COLOR
        return _MODIFIED_COLOR

    def _set_status(self, text, error=False):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            f"color: {'#E5534B' if error else theme.TEXT_DIM}; font-size: 12px;")

    def _update_controls(self):
        enabled = self._repo is not None
        for b in (self.stage_all_btn, self.unstage_all_btn,
                  self.commit_btn, self.push_btn, self.pull_btn):
            b.setEnabled(enabled)
