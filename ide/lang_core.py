"""Точка подключения ядра языка ZmeyGorynich к IDE.

Ядро (src/zmeygorynich) использует плоские импорты (from lexer import ...),
поэтому мы просто добавляем каталог ядра в sys.path и импортируем модули
напрямую, не меняя код самого языка.
"""
import os
import sys

_CORE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "zmeygorynich")
)
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from lexer import tokenize  # noqa: E402
from parser import parse, parse_with_errors, TYPE_MAP  # noqa: E402
from evaluator import Context, evaluate  # noqa: E402
from typecheck import (  # noqa: E402
    get_type_name,
    map_type_hint_to_display_name,
    stringify_value,
)
from zg_builtins import builtins as LANGUAGE_BUILTINS  # noqa: E402

__all__ = [
    "tokenize",
    "parse",
    "parse_with_errors",
    "TYPE_MAP",
    "Context",
    "evaluate",
    "get_type_name",
    "map_type_hint_to_display_name",
    "stringify_value",
    "LANGUAGE_BUILTINS",
]
