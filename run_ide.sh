#!/usr/bin/env bash
# Запуск IDE ZmeyGorynich (использует виртуальное окружение venv/).
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/venv"
if [ ! -x "$VENV/bin/python" ]; then
    echo "Виртуальное окружение не найдено ($VENV)." >&2
    echo "Создайте его: python3 -m venv venv && venv/bin/pip install -r requirements-ide.txt" >&2
    exit 1
fi
exec "$VENV/bin/python" "$DIR/scripts/run_ide.py" "$@"
