# Файл для теста кодировок и иных проблем эдитора/терминала
# Для поддержки рун закинуть в settings.json:
# "editor.fontFamily": "'Segoe UI Historic', 'DejaVu Sans', 'Fira Code', monospace"
# "terminal.integrated.fontFamily": "'Segoe UI Historic', 'DejaVu Sans', 'Fira Code', monospace",

import unicodedata

runes = "ᚠᚢᚦᚨᛚᛏ"

for char in runes:
    print(f"{char} - {unicodedata.name(char, 'UNKNOWN')}")