"""Панель управления git (source control) в стиле VS Code.

Показывает текущую ветку, список изменённых файлов с возможностью
поотдельного индексирования (чекбокс = файл проиндексирован), поле
сообщения коммита, а также кнопки commit / push / pull / refresh.

Все операции делегируются модулю :mod:`ide.git_backend`, который
вызывает системный git через subprocess.
"""
import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ide import theme
from ide.git_backend import GitRepo, GitError


_STAGED_COLOR = QColor("#73C991")
_MODIFIED_COLOR = QColor("#E6B450")
_UNTRACKED_COLOR = QColor("#9AA0A6")


class BranchTitle(QWidget):
    """Кликабельный заголовок с иконкой ветки и названием (с реальным gap)."""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GitBranchTitle")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)

        self._icon = QLabel()
        self._icon.setStyleSheet("background: transparent;")
        self._text = QLabel()
        self._text.setObjectName("GitBranchText")
        self._text.setStyleSheet(
            f"background: transparent; color: {theme.ACCENT}; "
            f"font-size: 18px; font-weight: 600;")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(8)
        lay.addWidget(self._icon)
        lay.addWidget(self._text, 1)

    def setText(self, text):
        self._text.setText(text)

    def setIconPixmap(self, pm):
        self._icon.setPixmap(pm)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


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

        # --- заголовок панели ---
        self.title_label = QLabel("Летописания")
        self.title_label.setObjectName("GitPanelTitle")
        root.addWidget(self.title_label)

        # --- сворачиваемая секция «Изменения» ---
        self._section_btn = QToolButton()
        self._section_btn.setObjectName("GitSection")
        self._section_btn.setText("▾ Изменения")
        self._section_btn.setCheckable(True)
        self._section_btn.setChecked(True)
        self._section_btn.clicked.connect(self._on_section_toggled)

        # --- контейнер изменений ---
        # Сам контейнер НИКОГДА не скрываем:
        # он всегда занимает всё оставшееся место панели.
        self._changes = QWidget()
        self._changes.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        changes_layout = QVBoxLayout(self._changes)
        changes_layout.setContentsMargins(0, 0, 0, 0)
        changes_layout.setSpacing(0)

        # Скрывать будем только содержимое.
        self._changes_content = QWidget()
        self._changes_content.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        cv = QVBoxLayout(self._changes_content)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(6)

        changes_layout.addWidget(self._changes_content, 1)

        # --- заголовок: текущая ветка (кнопка-переключатель), на всю ширину ---
        self.branch_btn = BranchTitle()
        self.branch_btn.setIconPixmap(self._branch_icon().pixmap(18, 18))
        self.branch_btn.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.branch_btn.clicked.connect(self._on_branch_clicked)
        cv.addWidget(self.branch_btn)

        # --- верхняя панель: действия ---
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(4)

        self.refresh_btn = self._tool("↻", "Обновить")
        self.refresh_btn.clicked.connect(self.refresh)
        self.stage_all_btn = self._tool("+", "Проиндексировать всё")
        self.stage_all_btn.clicked.connect(self._stage_all)
        self.unstage_all_btn = self._tool("−", "Убрать всё из индекса")
        self.unstage_all_btn.clicked.connect(self._unstage_all)
        self.push_btn = self._tool("⇡", "Отправить (push)")
        self.push_btn.clicked.connect(self._push)
        self.pull_btn = self._tool("⇣", "Забрать (pull)")
        self.pull_btn.clicked.connect(self._pull)

        for b in (self.refresh_btn, self.stage_all_btn, self.unstage_all_btn,
                  self.push_btn, self.pull_btn):
            top.addWidget(b)

        # строка заголовка: «Изменения» + действия справа
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(4)
        header.addWidget(self._section_btn)
        header.addStretch(1)
        header.addLayout(top)
        root.addLayout(header)

        root.addWidget(self._changes,1)


        # --- сообщение коммита ---
        self.commit_edit = QPlainTextEdit()
        self.commit_edit.setObjectName("GitCommit")
        self.commit_edit.setPlaceholderText("Сообщение коммита…")
        self.commit_edit.setMaximumHeight(56)
        cv.addWidget(self.commit_edit)

        # --- кнопка коммита на всю ширину ---
        self.commit_btn = QPushButton("✓  Коммит")
        self.commit_btn.setObjectName("GitCommitBtn")
        self.commit_btn.setFixedHeight(34)
        self.commit_btn.clicked.connect(self._commit)
        cv.addWidget(self.commit_btn)

        # --- список файлов ---
        self.list = QListWidget()
        self.list.setObjectName("GitList")
        self.list.setMinimumHeight(150)
        self.list.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        self.list.itemChanged.connect(self._on_item_changed)
        self.list.itemDoubleClicked.connect(self._on_item_double)
        cv.addWidget(self.list)

        # --- строка состояния ---
        self.status_label = QLabel("")
        self.status_label.setObjectName("GitStatus")
        self.status_label.setWordWrap(True)
        cv.addWidget(self.status_label)

        self._update_controls()

    def _tool(self, text, tooltip):
        btn = QToolButton()
        btn.setText(text)
        btn.setToolTip(tooltip)
        btn.setObjectName("GitTool")
        btn.setFixedSize(32, 32)
        return btn

    def _apply_style(self):
        self.setStyleSheet(
            f"""
            QWidget#GitBranchTitle {{
                background-color: {theme.BG_PANEL};
                border: 1px solid {theme.BORDER};
                border-radius: 6px;
            }}
            QWidget#GitBranchTitle:hover {{
                background-color: {theme.BG_ELEV};
                border: 1px solid {theme.ACCENT};
            }}
            QLabel#GitPanelTitle {{
                color: {theme.ACCENT};
                font-size: 17px;
                font-weight: 700;
                padding: 2px 0 4px 0;
            }}
            QToolButton#GitSection {{
                background: transparent;
                color: {theme.ACCENT};
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 700;
                text-align: left;
                padding: 3px 2px;
            }}
            QToolButton#GitSection:hover {{
                background-color: {theme.BG_ELEV};
                color: {theme.ACCENT_HOVER};
            }}
            QPushButton#GitCommitBtn {{
                background-color: {theme.ACCENT};
                color: #1B1B1F;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 700;
            }}
            QPushButton#GitCommitBtn:hover {{
                background-color: {theme.ACCENT_HOVER};
            }}
            QPushButton#GitCommitBtn:disabled {{
                background-color: {theme.BG_PANEL};
                color: {theme.TEXT_DIM};
                border: 1px solid {theme.BORDER};
            }}
            QToolButton#GitTool {{
                background: transparent;
                color: {theme.TEXT};
                border: none;
                border-radius: 6px;
                padding: 3px 9px;
                font-size: 14px;
            }}
            QToolButton#GitTool:hover {{
                background-color: {theme.BORDER};
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
            self.branch_btn.setText("не git-репозиторий")
            self.branch_btn.setEnabled(False)
            self.list.clear()
            self._set_status("Откройте папку внутри git-репозитория.", error=True)
            self._update_controls()
            return

        self._refreshing = True
        try:
            self.branch_btn.setText(self._repo.branch())
            self.branch_btn.setEnabled(True)
            files = self._repo.status()
        except GitError as exc:
            self._refreshing = False
            self.branch_btn.setText("—")
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

    def _on_section_toggled(self, checked):
        self._changes_content.setVisible(checked)

        self._section_btn.setText(
            ("▾ " if checked else "▸ ") + "Изменения"
        )

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

    # --- переключение веток ---

    def _on_branch_clicked(self):
        if self._repo is None:
            return

        try:
            branches = self._repo.branches()
        except GitError as exc:
            self._set_status(str(exc), error=True)
            return

        current = self._repo.branch()
        menu = QMenu(self)
        menu.setObjectName("GitBranchMenu")

        for name in branches:
            act = QAction(name, self)
            act.setCheckable(True)
            act.setChecked(name == current)
            act.triggered.connect(
                lambda _checked, n=name: self._switch_branch(n))
            menu.addAction(act)

        menu.addSeparator()
        new_act = QAction("＋ Создать ветку…", self)
        new_act.triggered.connect(self._create_branch)
        menu.addAction(new_act)

        menu.exec_(self.branch_btn.mapToGlobal(
            self.branch_btn.rect().bottomLeft()))

    def _switch_branch(self, name):
        try:
            out = self._repo.checkout(name)
        except GitError as exc:
            self._set_status(str(exc), error=True)
            return
        self._set_status(out or f"Переключено на ветку «{name}».")
        self.refresh()

    def _create_branch(self):
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            self, "Новая ветка", "Имя ветки:")
        name = (name or "").strip()
        if not ok or not name:
            return
        try:
            out = self._repo.create_branch(name)
        except GitError as exc:
            self._set_status(str(exc), error=True)
            return
        self._set_status(out or f"Создана и выбрана ветка «{name}».")
        self.refresh()

    def _branch_icon(self):
        pm = QPixmap(16, 16)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(theme.ACCENT), 2)
        p.setPen(pen)
        p.setBrush(QColor(theme.ACCENT))
        p.drawEllipse(2, 1, 5, 5)
        p.drawEllipse(2, 10, 5, 5)
        p.drawEllipse(11, 10, 5, 5)
        p.setBrush(Qt.NoBrush)
        p.drawLine(4, 6, 4, 10)
        p.drawLine(4, 13, 13, 13)
        p.end()
        return QIcon(pm)

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
