"""Справочник языка ZmeyGorynich — окно с описанием типов, операторов,
встроенных функций, управления потоком, переменных и ввода-вывода.

Данные собраны по ядру: src/zmeygorynich/{lexer,parser,evaluator,
zg_builtins,context,typecheck}.py.
"""
from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QListWidget, QListWidgetItem, QTextBrowser,
)
from PyQt5.QtCore import Qt

from ide.theme import BG, BG_PANEL, BORDER, TEXT, TEXT_DIM, ACCENT


_CODE = (
    'color:#C3E88D; font-family:"DejaVu Sans Mono","Consolas",monospace;'
)
_KW = 'color:#E6B450;'
_DIM = 'color:#9AA0A6;'


def _c(text):
    return f'<span style="{_CODE}">{text}</span>'


def _kw(text):
    return f'<span style="{_KW}">{text}</span>'


REFERENCE = {
    "Типы и числовые обозначения": f"""
<h2 style="{_KW}">Типы данных</h2>
<ul>
<li>{_kw('цело')} — целое число ({_c('int')}).</li>
<li>{_kw('плывун')} — число с плавающей точкой ({_c('float')}).</li>
<li>{_kw('плывун малый точный')} — десятичное с точностью 30 знаков ({_c('decimal(30)')}).</li>
<li>{_kw('плывун великий')} — десятичное с точностью 50 знаков.</li>
<li>{_kw('плывун звездный')} — десятичное с точностью 100 знаков.</li>
<li>{_kw('строченька')} — строка текста.</li>
<li>{_kw('двосуть')} — логическое значение {_c('истина')}/{_c('ложь')}.</li>
<li>{_kw('список цело')}, {_kw('список плывун')}, {_kw('список строченька')},
    {_kw('список двосуть')} — списки однотипных значений.</li>
</ul>

<h2 style="{_KW}">Числовые обозначения (литералы)</h2>
<ul>
<li>Целые: {_c('42')}, {_c('-7')}.</li>
<li>Дробные: {_c('3.14')}, {_c('0.5')}.</li>
<li>Экспоненциальная запись: {_c('1.5e10')}, {_c('2E-3')}.</li>
<li>Корень: {_kw('корешок из')} <i>число</i> — извлечение квадратного корня
    ({_c('корешок из 16  →  4')}).</li>
</ul>

<h2 style="{_KW}">Объявление с типом</h2>
<p>{_c('возраст быти цело = 25 гойда')}</p>
<p>{_c('пи быти плывун малый точный = 3.141592653589793238462643383279 гойда')}</p>
<p>Тип можно не указывать — он выведется из значения: {_c('имя = "Илья" гойда')}.</p>
""",

    "Переменные": f"""
<h2 style="{_KW}">Переменные</h2>
<ul>
<li>Объявление с типом: {_c('<имя> быти <тип> = <выражение> гойда')}.</li>
<li>Объявление без типа: {_c('<имя> = <выражение> гойда')}.</li>
<li>Присваивание элементу списка: {_c('<имя>[<индекс>] = <значение> гойда')}.</li>
</ul>
<p>Функции создают вложенный контекст, поэтому внутри функции видны переменные
извне, а объявленные внутри снаружи — нет (лексическая область видимости).</p>
<p>Обращение к элементу списка: {_c('список[0]')} (индексация с нуля).</p>
""",

    "Операторы": f"""
<h2 style="{_KW}">Арифметика</h2>
<table cellspacing="4">
<tr><td>{_c('+')}</td><td>прибави, плюс</td></tr>
<tr><td>{_c('-')}</td><td>отними, вычти, минус</td></tr>
<tr><td>{_c('*')}</td><td>умножи на, умножить на</td></tr>
<tr><td>{_c('/')}</td><td>раздели на, делить на</td></tr>
<tr><td>{_c('%')}</td><td>остаток от, мод</td></tr>
<tr><td>{_c('**')}</td><td>возвысить в, возвести в, в степенне</td></tr>
<tr><td>{_c('корешок из')}</td><td>квадратный корень</td></tr>
</table>

<h2 style="{_KW}">Сравнения</h2>
<table cellspacing="4">
<tr><td>{_c('==')}</td><td>ровно, равно, есть</td></tr>
<tr><td>{_c('!=')}</td><td>не равно, неравно, не есть</td></tr>
<tr><td>{_c('>')}</td><td>превосходит, превышает, больше</td></tr>
<tr><td>{_c('<')}</td><td>уступает, меньше, меньше чем</td></tr>
<tr><td>{_c('>=')}</td><td>ровно либо превосходит, больше или равно</td></tr>
<tr><td>{_c('<=')}</td><td>ровно либо уступает, меньше или равно</td></tr>
</table>

<h2 style="{_KW}">Логика</h2>
<p>{_c('и')} (and), {_c('или')} (or), {_c('не')} (not).</p>
<p>Строки складываются ({_c('"а" + "б"  →  "аб"')}), списки тоже
объединяются через {_c('+')}.</p>
""",

    "Встроенные функции": f"""
<h2 style="{_KW}">Вывод и отладка</h2>
<ul>
<li>{_kw('молвить')}(<i>выражение</i>) — напечатать значение.<br>
    форма {_c('молвить(...) и эхом затихнуть')} печатает с переводом строки.</li>
<li>{_kw('глас')}(<i>выражение</i>) — напечатать значение вместе с его типом
    и (для вызова функции) аргументами и типом возврата. Полезно для отладки.</li>
</ul>

<h2 style="{_KW}">Ввод</h2>
<ul>
<li>{_kw('внемли')}(<i>переменная</i>) — прочитать строку с клавиатуры и
    сохранить в переменную (значение приводится к числу/логике/строке).<br>
    с подсказкой: {_c('внемли("Как тебя звать? ", имя) гойда')}.</li>
</ul>

<h2 style="{_KW}">Работа со значениями</h2>
<ul>
<li>{_kw('созвать_дружину')}(<i>размер</i>, <i>значение</i>) — создать список
    заданного размера, заполненный значением
    ({_c('созвать_дружину(5, 0)')} → пять нулей).</li>
<li>{_kw('имя_аргумента')}() — имя аргумента/переменной (отладка).</li>
<li>{_kw('тип_значения')}(<i>значение</i>) — имя типа значения.</li>
<li>{_kw('строчить_значение')}(<i>значение</i>) — преобразовать значение в строку.</li>
</ul>
""",

    "Управление потоком": f"""
<h2 style="{_KW}">Условие</h2>
<p>{_c('аще <условие> ухожу я в пляс')}<br>
&nbsp;&nbsp;...<br>
{_c('закончили пляски')}<br>
{_c('ино аще <условие> ухожу я в пляс ... закончили пляски')} &nbsp;(иначе если)<br>
{_c('ино ухожу я в пляс ... закончили пляски')} &nbsp;(иначе)</p>

<h2 style="{_KW}">Циклы</h2>
<ul>
<li>{_kw('покуда')} <i>условие</i> {_c('ухожу я в пляс')} ... {_c('закончили пляски')}
    — пока условие истинно (while).</li>
<li>Фиксированные циклы: {_kw('дважды')}, {_kw('трижды')}, {_kw('четырежды')},
    {_kw('пятьжды')}, {_kw('шестьжды')}, {_kw('семьжды')}, {_kw('осьмьжды')},
    {_kw('девятьжды')}, {_kw('десятьжды')} (2–10 итераций) и {_kw('стожды')} (100).
    Тело в {_c('ухожу я в пляс ... закончили пляски')} или одна команда.</li>
</ul>

<h2 style="{_KW}">Функции</h2>
<p>{_c('сотвори <имя>(<arg> быти <тип>, ...) изречет <тип_возврата>')}<br>
{_c('ухожу я в пляс')}<br>
&nbsp;&nbsp;...<br>
&nbsp;&nbsp;{_c('возверни <выражение>')}<br>
{_c('закончили пляски')}</p>

<h2 style="{_KW}">Разделители и блоки</h2>
<ul>
<li>{_kw('гойда')} — конец оператора (как ; или новая строка).</li>
<li>{_kw('ухожу я в пляс')} / {_kw('закончили пляски')} — открытие/закрытие
    блока (фигурные скобки).</li>
<li>{_c('()')} — вызовы и группировка; {_c('[]')} — индексы списков.</li>
</ul>
""",

    "Импорт и модули": f"""
<h2 style="{_KW}">Импорт</h2>
<p>{_c('прочесть книгу "путь/файл.zg"')} — подключить функции и переменные
из другого .zg-файла (импортируются только функции и переменные).</p>
<p>С псевдонимом: {_c('прочесть книгу "lib.zg" и осмыслить слова как mylib')}.</p>
<p>Поиск файла: рядом с текущим файлом, затем в каталоге {_c('libs/')} выше.</p>
""",

    "Комментарии": f"""
<h2 style="{_KW}">Комментарии</h2>
<ul>
<li>Строчный: {_c('# текст')} — до конца строки.</li>
<li>Блочный: {_c('Голос предков шепчет: ... Голос предков внезапно стих...')}
    — многострочный, требует закрытия.</li>
</ul>
""",
}


class ReferenceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Справочник языка ZmeyGorynich")
        self.resize(780, 540)
        if parent is not None:
            self.setWindowModality(Qt.NonModal)

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        self.list_w = QListWidget()
        self.list_w.setObjectName("ReferenceList")
        self.list_w.setFixedWidth(230)
        for title in REFERENCE:
            self.list_w.addItem(QListWidgetItem(title))
        self.list_w.currentRowChanged.connect(self._show)

        self.browser = QTextBrowser()
        self.browser.setObjectName("ReferenceBrowser")
        self.browser.setOpenExternalLinks(False)
        self.browser.document().setDocumentMargin(14)

        root.addWidget(self.list_w, 0)
        root.addWidget(self.browser, 1)

        self._apply_style()
        self.list_w.setCurrentRow(0)

    def _apply_style(self):
        self.setStyleSheet(f"""
            QDialog {{ background-color: {BG}; }}
            QListWidget#ReferenceList {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER};
                border-radius: 6px;
                color: {TEXT};
                outline: 0;
            }}
            QListWidget#ReferenceList::item {{
                padding: 7px 10px;
                border-radius: 0;
            }}
            QListWidget#ReferenceList::item:selected {{
                background-color: #473B2C;
                color: {TEXT};
            }}
            QListWidget#ReferenceList::item:hover {{
                background-color: rgba(230,180,80,0.10);
            }}
            QTextBrowser#ReferenceBrowser {{
                background-color: {BG};
                border: 1px solid {BORDER};
                border-radius: 6px;
                color: {TEXT};
            }}
        """)
        self.browser.setStyleSheet(f"""
            QTextBrowser#ReferenceBrowser {{
                background-color: {BG};
                border: 1px solid {BORDER};
                border-radius: 6px;
                color: {TEXT};
                font-family: "DejaVu Sans", sans-serif;
                font-size: 13px;
            }}
        """)

    def _show(self, row):
        title = self.list_w.item(row).text()
        self.browser.setHtml(
            f'<div style="color:{TEXT};font-family:DejaVu Sans,sans-serif;">'
            f'{REFERENCE[title]}</div>'
        )
