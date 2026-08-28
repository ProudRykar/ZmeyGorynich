"""Современная тёмная «славянская» тема оформления (QSS + палитра Fusion).

Акцент — тёплое золото (#E6B450), фон — глубокий графит. Скруглённые панели,
тонкие разделители, кастомные скроллбары и шапка окна.
"""
import os

from PyQt5.QtGui import QColor, QFontDatabase, QPalette
from PyQt5.QtWidgets import QApplication


TITLE_FONT_FAMILY = None
SLOVIC_FAMILY = None

_FONTS_LOADED = False


def _load_custom_fonts():
    global TITLE_FONT_FAMILY, SLOVIC_FAMILY, _FONTS_LOADED
    if _FONTS_LOADED:
        return
    _FONTS_LOADED = True
    if QApplication.instance() is None:
        return
    base = os.path.dirname(__file__)

    balkara = os.path.join(base, "fonts", "BalkaraFreeCondensed.ttf")
    if os.path.exists(balkara):
        fid = QFontDatabase.addApplicationFont(balkara)
        families = QFontDatabase.applicationFontFamilies(fid)
        if families:
            TITLE_FONT_FAMILY = families[0]

    slovic = os.path.join(base, "fonts", "SPSL-New-Cyrillic", "spsl_new_cyrillic.ttf")
    if os.path.exists(slovic):
        fid = QFontDatabase.addApplicationFont(slovic)
        families = QFontDatabase.applicationFontFamilies(fid)
        if families:
            SLOVIC_FAMILY = families[0]



ACCENT = "#E6B450"
ACCENT_HOVER = "#F2C56A"
BG = "#1B1B1F"
BG_PANEL = "#232329"
BG_ELEV = "#2A2A31"
BORDER = "#5A4126"
BUTTON_COLOR = "#E6B450"
TEXT = "#E6E6E6"
TEXT_DIM = "#9AA0A6"
TITLE_BG = "#16161A"
TITLE_BTN_HOVER = "#5A4420"

QSS = f"""
QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: "__SLOVIC_FAMILY__", "Segoe UI", "Noto Sans", "Ubuntu", serif;
    font-size: 19px;
}}
QWidget#root, QWidget#central {{ background-color: {BG}; }}

/* --- шапка окна --- */
QWidget#TitleBar {{
    background-color: {TITLE_BG};
    border-bottom: 1px solid {BORDER};
}}
QLabel#TitleLabel {{
    color: {ACCENT};
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
    padding-left: 4px;
}}
QToolButton#TitleButton {{
    background-color: {TITLE_BG};
    color: {BUTTON_COLOR};
    border: none;
    border-radius: 5px;
    padding: 2px 8px;
    font-size: 14px;
}}
QToolButton#TitleButton:hover {{ background-color: {TITLE_BTN_HOVER}; }}
QToolButton#TitleRefButton, QToolButton#TitleMenuButton {{
    background-color: {TITLE_BG};
    color: {BUTTON_COLOR};
    border: none;
    border-radius: 5px;
    padding: 2px 8px;
    font-size: 20px;
}}
QToolButton#TitleRefButton:hover, QToolButton#TitleMenuButton:hover {{
    background-color: {TITLE_BTN_HOVER};
    border: none;
}}
QToolButton#TitleMenuButton::menu-indicator {{ image: none; width: 0; }}
QToolButton#TitleClose:hover {{ background-color: #C0392B; color: #FFFFFF; }}
QToolButton#RunButton {{
    background-color: {TITLE_BG};
    color: {BUTTON_COLOR};
    border: none;
    border-radius: 5px;
    padding: 2px 8px;
    font-size: 10px;
}}
QToolButton#RunButton:hover {{ background-color: rgba(230,180,80,0.18); }}

/* --- меню --- */
QMenuBar {{
    background-color: {TITLE_BG};
    color: {TEXT};
    padding: 2px 4px;
    border-bottom: 1px solid {BORDER};
}}
QMenuBar::item {{ padding: 4px 10px; border-radius: 4px; }}
QMenuBar::item:selected {{ background-color: {BG_ELEV}; }}
QMenu {{
    background-color: {BG_PANEL};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px;
}}
QMenu::item {{ padding: 5px 18px 5px 12px; border-radius: 4px; }}
QMenu::item:selected {{ background-color: {ACCENT}; color: #1B1B1F; }}
QMenu::separator {{ height: 1px; background: {BORDER}; margin: 4px 6px; }}

/* --- тулбар --- */
QToolBar {{
    background-color: {TITLE_BG};
    border: none;
    spacing: 6px;
    padding: 6px 8px;
}}
QToolButton {{
    background-color: {BG_PANEL};
    color: {BUTTON_COLOR};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 13px;
}}
QToolButton:hover {{ background-color: {BG_ELEV}; border: 1px solid {ACCENT}; }}
QToolButton:pressed {{ background-color: {BORDER}; }}
QToolButton:disabled {{ color: {BUTTON_COLOR}; background-color: {BG}; border: 1px solid {BORDER}; opacity: 0.5; }}

/* --- вкладки редактора --- */
QTabWidget::pane {{ background-color: {BG}; border: 1px solid {BORDER}; top: -1px; }}
QTabWidget > QWidget {{ background-color: {BG}; }}
QTabBar::tab {{
    background-color: {BG_PANEL};
    color: {TEXT_DIM};
    padding: 7px 16px;
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 3px;
}}
QTabBar::tab:selected {{
    background-color: {BG};
    color: {TEXT};
    border-top: 2px solid {ACCENT};
}}
QTabBar::tab:!selected:hover {{ background-color: {BG_ELEV}; color: {TEXT}; }}
QTabBar::close-button {{
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHdpZHRoPScxMCcgaGVpZ2h0PScxMCc+PHBhdGggZD0nTTIgMiBMOCA4IE04IDIgTDIgOCcgc3Ryb2tlPScjRTZCNDUwJyBzdHJva2Utd2lkdGg9JzEuNCcgc3Ryb2tlLWxpbmVjYXA9J3JvdW5kJy8+PC9zdmc+);
    subcontrol-position: right;
    padding: 2px;
}}

/* --- активити-бар (значки слева, как в VS Code) --- */
QWidget#Sidebar {{ background-color: {BG_PANEL}; }}
QWidget#ActivityBar {{
    background-color: {TITLE_BG};
    border-right: 1px solid {BORDER};
}}
QToolButton#ActivityButton {{
    background: transparent;
    border: none;
    border-left: 2px solid transparent;
    border-radius: 0;
    padding: 0;
}}
QToolButton#ActivityButton:hover {{ background-color: {BG_ELEV}; }}
QToolButton#ActivityButton:checked {{
    background-color: {BG_ELEV};
    border-left: 2px solid {ACCENT};
}}
QWidget#SidebarHeader {{
    background-color: {TITLE_BG};
    border-bottom: 1px solid {BORDER};
}}
QLabel#SidebarTitle {{
    color: {TEXT_DIM};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 4px;
}}
QToolButton#SidebarToggle {{
    background-color: transparent; color: {TEXT_DIM}; border: none;
    border-radius: 4px; padding: 2px 8px;
}}
QToolButton#SidebarToggle:hover {{ background-color: {BG_ELEV}; color: {TEXT}; }}

/* --- списки и дерево --- */
QListWidget, QTreeWidget {{
    background-color: {BG_PANEL};
    border: none;
    color: {TEXT};
    outline: 0;
}}
QListWidget {{ show-decoration-selected: 1; }}
QTreeWidget {{ show-decoration-selected: 1; }}
QListWidget::item {{
    padding: 5px 8px;
    border-radius: 6px;
}}
QTreeWidget::item {{
    padding: 5px 8px 5px 0;
    border-radius: 0;
}}
QListWidget::item:hover, QTreeWidget::item:hover {{ background-color: {BG_ELEV}; }}
QListWidget::item:selected, QTreeWidget::item:selected {{
    background-color: #473B2C;
    color: {TEXT};
}}
QTreeWidget::branch {{ background-color: transparent; }}
QHeaderView::section {{
    background-color: {TITLE_BG}; color: {TEXT_DIM};
    border: none; padding: 4px;
}}

/* --- вывод / проблемы --- */
QPlainTextEdit, QTextEdit {{
    background-color: {BG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    color: {TEXT};
    font-family: "DejaVu Sans Mono", "Consolas", monospace;
    font-size: 12px;
}}

/* --- разделители --- */
QSplitter::handle {{ background-color: {BORDER}; }}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical {{ height: 1px; }}

/* --- статус-бар --- */
QStatusBar {{
    background-color: {TITLE_BG};
    color: {TEXT_DIM};
    border-top: 1px solid {BORDER};
    padding: 3px 8px;
}}
QLabel#StatusText {{ color: {TEXT}; }}
QToolButton#StatusAccent {{
    background: transparent;
    border: none;
    color: {BUTTON_COLOR};
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 4px;
}}
QToolButton#StatusAccent:hover {{ background-color: rgba(230,180,80,0.15); }}
QSizeGrip {{ background: transparent; width: 14px; height: 14px; }}

/* --- кнопки запуска/остановки в углу вкладок --- */
QToolButton#RunButton, QToolButton#StopButton {{
    background: transparent;
    border: none;
    border-radius: 6px;
    color: {TEXT};
    font-size: 13px;
    padding: 0;
}}
QToolButton#RunButton:hover, QToolButton#StopButton:hover {{
    background-color: {TITLE_BTN_HOVER};
}}
QToolButton#StopButton:disabled {{ color: {TEXT_DIM}; }}

/* --- скроллбары --- */
QScrollBar:vertical {{
    background: {BG_PANEL}; width: 10px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER}; border-radius: 5px; min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {TEXT_DIM}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {BG_PANEL}; height: 10px; margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER}; border-radius: 5px; min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{ background: {TEXT_DIM}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* горизонтальный скролл редактора — тоньше */
QsciScintilla QScrollBar:horizontal {{
    height: 6px;
    background: {BG_PANEL};
}}
QsciScintilla QScrollBar::handle:horizontal {{
    min-width: 20px;
}}

/* --- всплывающие подсказки --- */
QToolTip {{
    background-color: {BG_ELEV};
    color: {TEXT};
    border: 1px solid {ACCENT};
    border-radius: 6px;
    padding: 5px 8px;
}}
"""


def _palette():
    p = QPalette()
    p.setColor(QPalette.Window, QColor(BG))
    p.setColor(QPalette.WindowText, QColor(TEXT))
    p.setColor(QPalette.Base, QColor(BG_PANEL))
    p.setColor(QPalette.AlternateBase, QColor(BG_ELEV))
    p.setColor(QPalette.Text, QColor(TEXT))
    p.setColor(QPalette.Button, QColor(BG_PANEL))
    p.setColor(QPalette.ButtonText, QColor(TEXT))
    p.setColor(QPalette.Highlight, QColor("#473B2C"))
    p.setColor(QPalette.HighlightedText, QColor(TEXT))
    p.setColor(QPalette.ToolTipBase, QColor(BG_ELEV))
    p.setColor(QPalette.ToolTipText, QColor(TEXT))
    p.setColor(QPalette.PlaceholderText, QColor(TEXT_DIM))
    return p


UI_FONT_FALLBACK = "\"Segoe UI\", \"Noto Sans\", \"Ubuntu\", sans-serif"
MONO_FALLBACK = "\"DejaVu Sans Mono\", \"Consolas\", \"Monaco\", monospace"

EXCLUDE_RULES = """
QWidget#ProblemsList {
    font-family: __UI_FONT_FALLBACK__;
    font-size: 13px;
}
QPlainTextEdit#TerminalView {
    font-family: __MONO_FALLBACK__;
    font-size: 13px;
}
"""

DRAGON_RULE = """
QWidget#ProblemsList, QPlainTextEdit#TerminalView {
    background-color: transparent;
    background-image: url(__DRAGON_URL__);
    background-repeat: no-repeat;
    background-position: right bottom;
}
"""


def apply_theme(app: QApplication):
    _load_custom_fonts()
    app.setStyle("Fusion")
    app.setPalette(_palette())
    slovic = SLOVIC_FAMILY or "Segoe UI"
    base_qss = QSS.replace("__SLOVIC_FAMILY__", slovic)
    exclude_qss = EXCLUDE_RULES.replace("__UI_FONT_FALLBACK__", UI_FONT_FALLBACK).replace(
        "__MONO_FALLBACK__", MONO_FALLBACK)
    dragon_path = os.path.join(os.path.dirname(__file__), "img", "dragon_bg.png").replace("\\", "/")
    dragon_qss = ""
    if os.path.exists(dragon_path):
        dragon_qss = DRAGON_RULE.replace("__DRAGON_URL__", dragon_path)
    title_rule = ""
    if TITLE_FONT_FAMILY:
        title_rule = (
            "\nQLabel#TitleLabel {{\n"
            "    font-family: \"{0}\";\n"
            "    font-size: 18px;\n"
            "    font-weight: normal;\n"
            "}}\n"
        ).format(TITLE_FONT_FAMILY)
    app.setStyleSheet(base_qss + exclude_qss + dragon_qss + title_rule)
