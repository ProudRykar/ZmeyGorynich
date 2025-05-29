## Запуск программы

Для запуска программы на языке Zmey Gorynich используется следующая команда:

```bash
python -m logic/interpreter.py examples/program.zg
```

- **Аргументы**:
  - `logic/interpreter.py` — путь к интерпретатору.
  - `examples/program.zg` — путь к файлу с кодом на языке Zmey Gorynich.
- **Требования**:
  - Установленный Python 3.x.
  - Библиотека `colorama` для цветного вывода.
  - Файл с кодом должен иметь расширение `.zg`.

Если файл не имеет расширения `.zg`, интерпретатор выдаст ошибку:

```
Error: filename is not a valid ZmeyGorynich file!
```