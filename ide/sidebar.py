"""Боковая панель в стиле VS Code: активити-бар со значками слева,
а справа от него — соответствующая панель (проводник файлов / символы)."""
import math
import os

from PyQt5.QtCore import pyqtSignal, Qt, QSize, QByteArray
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import (
    QApplication, QCheckBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QSpinBox, QStackedWidget, QToolButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

from ide.editor.zg_editor import ZGEditor
from ide import theme

ACCENT = "#E6B450"


class Sidebar(QWidget):
    fileActivated = pyqtSignal(str)        # путь к файлу
    symbolActivated = pyqtSignal(tuple)    # (line, col)
    openFolderRequested = pyqtSignal()
    settingsChanged = pyqtSignal(dict)     # изменения настроек IDE

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(0)

        # --- активити-бар (значки слева) ---
        self.activity_bar = QWidget()
        self.activity_bar.setObjectName("ActivityBar")
        self.activity_bar.setFixedWidth(52)
        ab = QVBoxLayout(self.activity_bar)
        ab.setContentsMargins(0, 6, 0, 0)
        ab.setSpacing(4)
        self._activity_buttons = []

        # --- контент (сменяемые панели) ---
        self._content = QStackedWidget()
        self._files_view = self._build_files_view()
        self._symbols_view = self._build_symbols_view()
        self._search_view = self._build_search_view()
        self._settings_view = self._build_settings_view()
        self._content.addWidget(self._files_view)
        self._content.addWidget(self._symbols_view)
        self._content.addWidget(self._search_view)
        self._content.addWidget(self._settings_view)

        self._add_activity(self._folder_icon(),
                           "Проводник (файлы)", self._files_view)
        self._add_activity(self._symbol_icon(),
                           "Символы (функции/переменные)", self._symbols_view)
        self._add_activity(self._search_icon(),
                           "Поиск и замена", self._search_view)
        self._add_activity(self._settings_icon(),
                           "Настройки IDE", self._settings_view)

        # поставщик текущего редактора (устанавливается из MainWindow)
        self.current_editor_provider = None

        ab.addStretch(1)
        self._deco = self._build_deco()
        ab.addWidget(self._deco, alignment=Qt.AlignHCenter)

        top.addWidget(self.activity_bar)
        top.addWidget(self._content, 1)
        root.addLayout(top, 1)
        self._set_active(0)

    # ---------- активити-бар ----------
    def _add_activity(self, icon, tip, widget):
        btn = QToolButton()
        btn.setObjectName("ActivityButton")
        btn.setIcon(icon)
        btn.setIconSize(QSize(22, 22))
        btn.setToolTip(tip)
        btn.setCheckable(True)
        btn.setFixedSize(44, 44)
        btn.clicked.connect(lambda _, w=widget, b=btn: self._activate(w, b))
        self.activity_bar.layout().addWidget(btn, alignment=Qt.AlignHCenter)
        self._activity_buttons.append(btn)

    def _activate(self, widget, btn):
        for b in self._activity_buttons:
            b.setChecked(b is btn)
        self._content.setCurrentWidget(widget)

    def _set_active(self, index):
        self._activate(self._content.widget(index), self._activity_buttons[index])

    # ---------- декоративный вектор внизу активити-бара ----------
    def _build_deco(self):
        label = QLabel()
        label.setObjectName("SidebarDeco")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("background: transparent;")
        col_w = self.activity_bar.width() or 52
        path = os.path.join(os.path.dirname(__file__), "img",
                           "vecteezy_circle-decoration_36645819.svg")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                svg = f.read()
            c = QColor(theme.BORDER)
            svg = svg.replace("rgb(204,204,204)",
                             f"rgb({c.red()}, {c.green()}, {c.blue()})")
            renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
            size = col_w - 8
            pm = QPixmap(size, size)
            pm.fill(Qt.transparent)
            p = QPainter(pm)
            p.setRenderHint(QPainter.Antialiasing)
            renderer.render(p)
            p.end()
            label.setPixmap(pm)
        label.setFixedSize(col_w, col_w)
        return label

    def _symbol_icon(self):
        pm = QPixmap(24, 24)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setPen(QColor(ACCENT))
        p.setFont(QFont("DejaVu Sans", 16, QFont.Bold))
        p.drawText(pm.rect(), Qt.AlignCenter, "ƒ")
        p.end()
        return QIcon(pm)

    def _folder_icon(self):
        pm = QPixmap(24, 24)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(ACCENT), 2)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(QColor(ACCENT))
        p.drawRoundedRect(3, 9, 18, 11, 2, 2)      # корпус папки
        p.setBrush(QColor("#16161A"))
        p.drawRect(3, 9, 18, 4)                    # «открытая» верхняя часть
        p.setBrush(QColor(ACCENT))
        p.drawRoundedRect(3, 6, 9, 4, 1, 1)        # язычок папки
        p.end()
        return QIcon(pm)

    def _file_icon(self, path):
        ext = os.path.splitext(path)[1].lower()
        color = {
            ".zg": ACCENT,
            ".py": "#4EC9B0",
        }.get(ext, "#9AA0A6")
        pm = QPixmap(24, 24)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(color), 2)
        p.setPen(pen)
        p.setBrush(QColor("#2A2A31"))
        p.drawRoundedRect(5, 4, 14, 16, 2, 2)      # тело документа
        p.setBrush(QColor(color))
        p.drawRect(12, 4, 7, 5)                    # загнутый уголок
        p.end()
        return QIcon(pm)

    def _search_icon(self):
        pm = QPixmap(24, 24)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(ACCENT), 2)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(6, 6, 11, 11)                 # лупа
        p.drawLine(15, 15, 20, 20)                 # ручка
        p.end()
        return QIcon(pm)

    def _settings_icon(self):
        pm = QPixmap(24, 24)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(ACCENT), 2)
        p.setPen(pen)
        p.setBrush(QColor(ACCENT))
        cx, cy, r = 12, 12, 5
        p.drawEllipse(cx - r, cy - r, 2 * r, 2 * r)  # центр шестерёнки
        p.setBrush(Qt.NoBrush)
        for i in range(8):                          # зубцы
            ang = i * math.pi / 4
            x1, y1 = cx + (r + 1) * math.cos(ang), cy + (r + 1) * math.sin(ang)
            x2, y2 = cx + (r + 4) * math.cos(ang), cy + (r + 4) * math.sin(ang)
            p.drawLine(int(x1), int(y1), int(x2), int(y2))
        p.end()
        return QIcon(pm)

    # ---------- панель проводника (дерево папок) ----------
    def _build_files_view(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        hdr = QWidget()
        hrow = QHBoxLayout(hdr)
        hrow.setContentsMargins(10, 6, 8, 6)
        hrow.setSpacing(6)
        title = QLabel("ПРОВОДНИК")
        title.setObjectName("SidebarTitle")
        hrow.addWidget(title)
        v.addWidget(hdr)

        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setRootIsDecorated(False)
        self.file_tree.setIndentation(16)
        self.file_tree.itemClicked.connect(self._on_file_activated)
        self.file_tree.itemExpanded.connect(self._on_expanded)
        v.addWidget(self.file_tree, 1)
        return w

    # ---------- панель символов ----------
    def _build_symbols_view(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        hdr = QLabel("СИМВОЛЫ")
        hdr.setObjectName("SidebarTitle")
        hdr.setContentsMargins(10, 8, 0, 8)
        v.addWidget(hdr)
        self.symbol_tree = QTreeWidget()
        self.symbol_tree.setHeaderHidden(True)
        self.symbol_tree.itemDoubleClicked.connect(self._on_symbol_activated)
        v.addWidget(self.symbol_tree, 1)
        return w

    # ---------- панель поиска/замены ----------
    def _build_search_view(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(6)

        title = QLabel("ПОИСК И ЗАМЕНА")
        title.setObjectName("SidebarTitle")
        v.addWidget(title)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Найти…")
        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("Заменить на…")
        v.addWidget(self.search_edit)
        v.addWidget(self.replace_edit)

        row = QHBoxLayout()
        row.setSpacing(4)
        b_find = QToolButton(); b_find.setText("Найти")
        b_next = QToolButton(); b_next.setText("Далее ▾")
        b_prev = QToolButton(); b_prev.setText("Назад ▴")
        row.addWidget(b_find); row.addWidget(b_prev); row.addWidget(b_next)
        v.addLayout(row)

        row2 = QHBoxLayout()
        row2.setSpacing(4)
        b_rep = QToolButton(); b_rep.setText("Заменить")
        b_repall = QToolButton(); b_repall.setText("Заменить всё")
        row2.addWidget(b_rep); row2.addWidget(b_repall)
        v.addLayout(row2)

        self.search_status = QLabel("")
        self.search_status.setObjectName("StatusText")
        v.addWidget(self.search_status)
        v.addStretch(1)

        b_find.clicked.connect(lambda: self._do_find(True))
        b_next.clicked.connect(lambda: self._do_find_next())
        b_prev.clicked.connect(lambda: self._do_find(False))
        b_rep.clicked.connect(self._do_replace)
        b_repall.clicked.connect(self._do_replace_all)
        self.search_edit.returnPressed.connect(lambda: self._do_find(True))
        self.replace_edit.returnPressed.connect(self._do_replace)
        return w

    def _current_editor(self):
        if self.current_editor_provider is not None:
            return self.current_editor_provider()
        return None

    def _do_find(self, forward):
        ed = self._current_editor()
        if ed is None or not self.search_edit.text():
            return False
        ok = ed.findFirst(self.search_edit.text(), False, False, False,
                         True, forward, -1, -1, True)
        self._search_ok = ok
        self.search_status.setText("Найдено" if ok else "Не найдено")
        return ok

    def _do_find_next(self):
        ed = self._current_editor()
        if ed is None:
            return
        if getattr(self, "_search_ok", False):
            ok = ed.findNext()
            self.search_status.setText("Найдено" if ok else "Больше совпадений нет")
        else:
            self._do_find(True)

    def _do_replace(self):
        ed = self._current_editor()
        if ed is None:
            return
        if not getattr(self, "_search_ok", False):
            if not self._do_find(True):
                return
        ed.replace(self.replace_edit.text())
        self._search_ok = False
        self._do_find(True)

    def _do_replace_all(self):
        ed = self._current_editor()
        if ed is None or not self.search_edit.text():
            return
        text = self.search_edit.text()
        repl = self.replace_edit.text()
        count = 0
        ed.beginUndoAction()
        if ed.findFirst(text, False, False, False, True, True, -1, -1, True):
            while True:
                ed.replace(repl)
                count += 1
                if not ed.findNext():
                    break
        ed.endUndoAction()
        self._search_ok = False
        self.search_status.setText(f"Заменено: {count}")

    # ---------- панель настроек ----------
    def _build_settings_view(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(8)

        title = QLabel("НАСТРОЙКИ IDE")
        title.setObjectName("SidebarTitle")
        v.addWidget(title)

        fl = QHBoxLayout()
        fl.setSpacing(6)
        fl.addWidget(QLabel("Размер шрифта редактора:"))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 28)
        self.font_spin.setValue(getattr(ZGEditor, "default_font_size", 11))
        fl.addWidget(self.font_spin)
        v.addLayout(fl)

        self.ln_check = QCheckBox("Показывать номера строк")
        self.ln_check.setChecked(True)
        v.addWidget(self.ln_check)

        apply = QToolButton()
        apply.setText("Применить")
        apply.clicked.connect(self._emit_settings)
        v.addWidget(apply)
        v.addStretch(1)
        return w

    def _emit_settings(self):
        self.settingsChanged.emit({
            "font_size": self.font_spin.value(),
            "show_line_numbers": self.ln_check.isChecked(),
        })

    # ---------- проводник (дерево) ----------
    def set_root(self, path):
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            if os.path.isfile(path):
                path = os.path.dirname(path)
            else:
                return
        self._root_path = path
        self.file_tree.clear()
        root = QTreeWidgetItem(self.file_tree, [os.path.basename(path)])
        root.setIcon(0, self._folder_icon())
        root.setData(0, Qt.UserRole, path)
        root.setData(0, Qt.UserRole + 1, True)     # это каталог
        root.setData(0, Qt.UserRole + 2, False)    # ещё не заполнен
        self.file_tree.addTopLevelItem(root)
        self._populate_children(path, root)
        root.setData(0, Qt.UserRole + 2, True)
        self.file_tree.expandItem(root)

    def _populate_children(self, dir_path, parent_item):
        try:
            names = sorted(os.listdir(dir_path))
        except OSError:
            return
        dirs = [n for n in names if os.path.isdir(os.path.join(dir_path, n))]
        files = [n for n in names
                 if os.path.isfile(os.path.join(dir_path, n))
                 and (n.endswith(".zg") or n.endswith(".py"))]
        for d in dirs:
            full = os.path.join(dir_path, d)
            it = QTreeWidgetItem(parent_item, [d])
            it.setIcon(0, self._folder_icon())
            it.setData(0, Qt.UserRole, full)
            it.setData(0, Qt.UserRole + 1, True)
            it.setData(0, Qt.UserRole + 2, False)
            it.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
        for f in files:
            full = os.path.join(dir_path, f)
            it = QTreeWidgetItem(parent_item, [f])
            it.setIcon(0, self._file_icon(full))
            it.setData(0, Qt.UserRole, full)
            it.setData(0, Qt.UserRole + 1, False)

    def _on_expanded(self, item):
        if item.data(0, Qt.UserRole + 1) is True and not item.data(0, Qt.UserRole + 2):
            self._populate_children(item.data(0, Qt.UserRole), item)
            item.setData(0, Qt.UserRole + 2, True)

    def _on_file_activated(self, item):
        path = item.data(0, Qt.UserRole)
        if not path:
            return
        if item.data(0, Qt.UserRole + 1) is True:
            if item.isExpanded():
                self.file_tree.collapseItem(item)
            else:
                self.file_tree.expandItem(item)
            return
        self.fileActivated.emit(path)

    # ---------- символы ----------
    def set_symbols(self, symbols):
        self.symbol_tree.clear()
        self._func_root = QTreeWidgetItem(self.symbol_tree, ["Функции"])
        self._var_root = QTreeWidgetItem(self.symbol_tree, ["Переменные"])
        self._func_root.setExpanded(True)
        self._var_root.setExpanded(True)
        if symbols is None:
            return
        for name, sym in symbols.functions.items():
            label = f"{name}({', '.join(a[0] for a in sym.args)})"
            item = QTreeWidgetItem(self._func_root, [label])
            item.setData(0, Qt.UserRole, (sym.line, sym.col))
        for name, sym in symbols.variables.items():
            item = QTreeWidgetItem(self._var_root, [name])
            item.setData(0, Qt.UserRole, (sym.line, sym.col))
        self._func_root.setText(0, f"Функции ({self._func_root.childCount()})")
        self._var_root.setText(0, f"Переменные ({self._var_root.childCount()})")

    def _on_symbol_activated(self, item):
        data = item.data(0, Qt.UserRole)
        if data:
            self.symbolActivated.emit(data)
