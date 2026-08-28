"""Кастомный лексер подсветки для QScintilla.

Не зависит от строгого лексера языка (tokenize), а сканирует текст
толерантным регулярным выражением, зеркалящим грамматику из
zmey-gorynich-syntax/syntaxes/zmeygorynich.tmLanguage.json. Это позволяет
корректно подсвечивать незавершённый код при наборе.
"""
import re

from PyQt5.Qsci import QsciLexerCustom
from PyQt5.QtGui import QColor, QFont, QFontDatabase


def mono_family():
    """Подобрать моноширинный шрифт с кириллицей и жирным/курсивом.

    Generic 'Monospace' при запросе bold подменяется на другой физический
    шрифт, который может не содержать кириллицу -> глифы рендерятся с
    "лишними" пробелами. Берём конкретный шрифт, гарантированно имеющий
    кириллический bold/italic.
    """
    try:
        families = set(QFontDatabase().families())
    except Exception:
        families = set()
    candidates = [
        "DejaVu Sans Mono", "Liberation Mono", "Ubuntu Mono",
        "Consolas", "Courier New", "Noto Sans Mono", "Monospace",
    ]
    for fam in candidates:
        if fam in families:
            return fam
    return "Monospace"


def _mono_font(bold=False, italic=False):
    f = QFont(mono_family(), 11)
    f.setStyleHint(QFont.Monospace)
    f.setFixedPitch(True)
    f.setKerning(False)
    f.setBold(bold)
    f.setItalic(italic)
    return f

# Идентификаторы стилей
STYLE_DEFAULT = 0
STYLE_KEYWORD = 1
STYLE_TYPE = 2
STYLE_BUILTIN = 3
STYLE_STRING = 4
STYLE_NUMBER = 5
STYLE_COMMENT = 6
STYLE_OP = 7
STYLE_BRACE = 8
STYLE_GOYDA = 9
STYLE_IDENT = 10

# Цвета (тёмная "славянская" палитра)
COLORS = {
    STYLE_DEFAULT: "#E6E6E6",
    STYLE_KEYWORD: "#FFCB6B",
    STYLE_TYPE: "#F78C6C",
    STYLE_BUILTIN: "#C792EA",
    STYLE_STRING: "#C3E88D",
    STYLE_NUMBER: "#82AAFF",
    STYLE_COMMENT: "#6A9955",
    STYLE_OP: "#89DDFF",
    STYLE_BRACE: "#F78C6C",
    STYLE_GOYDA: "#7F848E",
    STYLE_IDENT: "#B0C9FF",
}

_BOLD = {STYLE_KEYWORD, STYLE_TYPE, STYLE_BRACE}
_ITALIC = {STYLE_COMMENT, STYLE_GOYDA}


class ZGLexer(QsciLexerCustom):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_patterns()
        paper = QColor("#1B1B1F")
        for style, color in COLORS.items():
            self.setColor(QColor(color), style)
            self.setPaper(paper, style)
            self.setFont(_mono_font(bold=style in _BOLD, italic=style in _ITALIC), style)
        self.setDefaultColor(QColor(COLORS[STYLE_DEFAULT]))
        self.setDefaultPaper(paper)

    def _build_patterns(self):
        patterns = [
            ("COMMENT", r"#[^\n]*"),
            ("BLOCKCOMMENT", r"Голос предков шепчет:.*?Голос предков внезапно стих\.\.\."),
            ("STRING", r"\"(?:[^\"\\]|\\.)*\""),
            ("BRACEOPEN", r"ухожу я в пляс"),
            ("BRACECLOSE", r"закончили пляски"),
            ("AS", r"и осмыслить слова как"),
            ("SILENT", r"и эхом затихнуть"),
            ("ROOT", r"корешок из"),
            ("GOYDA", r"гойда"),
            ("TYPEANN", r"быти"),
            ("DEF", r"сотвори"),
            ("RETURNTYPE", r"изречет"),
            ("RETURN", r"возверни"),
            ("IMPORT", r"прочесть книгу"),
            ("KEYWORD", r"(?<!\w)(?:покуда|молвить|внемли|ино|аще|ли|то|глас|созвать_дружину|не|или|и|Истина|Ложь|дважды|трижды|четырежды|пятьжды|шестьжды|семьжды|осьмьжды|девятьжды|десятьжды|стожды)(?!\w)"),
            ("TYPE", r"(?<!\w)(?:плывун малый точный|плывун великий|плывун звездный|список цело|список плывун|список строченька|список двосуть|цело|строченька|двосуть|плывун|список)(?!\w)"),
            ("BUILTIN", r"(?<!\w)(?:тип_значения|строчить_значение|имя_аргумента)(?!\w)"),
            ("NUMBER", r"\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"),
            ("OP", r"возвысить в|прибави|отними|умножи на|раздели на|остаток от|ровно либо превосходит|ровно либо уступает|превосходит|уступает|равно|не равно|есть|отлично|\*\*|[+\-*/%]|[<>]=?|!=|=="),
            ("DOT", r"\."),
            ("ASSIGN", r"="),
            ("COMMA", r","),
            ("BRACKET", r"[\[\]]"),
            ("PAREN", r"[()]"),
            ("ID", r"[A-Za-z\u0400-\u04FF\u16A0-\u16FF_][A-Za-z\u0400-\u04FF\u16A0-\u16FF_0-9]*"),
            ("SPACE", r"\s+"),
        ]
        self._master = re.compile(
            "|".join(f"(?P<{name}>{pat})" for name, pat in patterns),
            re.DOTALL,
        )
        self._style_map = {
            "COMMENT": STYLE_COMMENT,
            "BLOCKCOMMENT": STYLE_COMMENT,
            "STRING": STYLE_STRING,
            "BRACEOPEN": STYLE_BRACE,
            "BRACECLOSE": STYLE_BRACE,
            "AS": STYLE_KEYWORD,
            "SILENT": STYLE_KEYWORD,
            "ROOT": STYLE_KEYWORD,
            "GOYDA": STYLE_GOYDA,
            "TYPEANN": STYLE_TYPE,
            "DEF": STYLE_KEYWORD,
            "RETURNTYPE": STYLE_KEYWORD,
            "RETURN": STYLE_KEYWORD,
            "IMPORT": STYLE_KEYWORD,
            "KEYWORD": STYLE_KEYWORD,
            "TYPE": STYLE_TYPE,
            "BUILTIN": STYLE_BUILTIN,
            "NUMBER": STYLE_NUMBER,
            "OP": STYLE_OP,
            "DOT": STYLE_DEFAULT,
            "ASSIGN": STYLE_OP,
            "COMMA": STYLE_DEFAULT,
            "BRACKET": STYLE_DEFAULT,
            "PAREN": STYLE_DEFAULT,
            "ID": STYLE_IDENT,
            "SPACE": STYLE_DEFAULT,
        }

    def language(self):
        return "ZmeyGorynich"

    def description(self, style):
        names = {
            STYLE_DEFAULT: "Default",
            STYLE_KEYWORD: "Keyword",
            STYLE_TYPE: "Type",
            STYLE_BUILTIN: "Builtin",
            STYLE_STRING: "String",
            STYLE_NUMBER: "Number",
            STYLE_COMMENT: "Comment",
            STYLE_OP: "Operator",
            STYLE_BRACE: "Brace",
            STYLE_GOYDA: "Goyda",
            STYLE_IDENT: "Identifier",
        }
        return names.get(style, "Unknown")

    def styleText(self, start, end):
        editor = self.editor()
        if editor is None:
            return
        text = editor.text()
        # Scintilla хранит UTF-8 текст и измеряет позиции/длины стилизации в
        # БАЙТАХ. Кириллица — 2 байта/символ, поэтому длины считаем в байтах,
        # иначе стилизация «убегает» и текст визуально рассыпается пробелами.
        self.startStyling(0)
        pos = 0
        n = len(text)
        while pos < n:
            m = self._master.match(text, pos)
            if not m:
                tok = text[pos]
                self.setStyling(len(tok.encode("utf-8")), STYLE_DEFAULT)
                pos += 1
                continue
            tok = m.group(0)
            style = self._style_map.get(m.lastgroup, STYLE_DEFAULT)
            self.setStyling(len(tok.encode("utf-8")), style)
            pos += len(tok)
