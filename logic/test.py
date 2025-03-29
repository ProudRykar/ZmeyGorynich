# Файл для теста кодировок и иных проблем эдитора/терминала
import unicodedata

runes = "ᚠᚢᚦᚨᛚᛏ"

for char in runes:
    print(f"{char} - {unicodedata.name(char, 'UNKNOWN')}")