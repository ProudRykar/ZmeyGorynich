"""Точка входа IDE ZmeyGorynich."""
import sys

try:
    from PyQt5.QtWidgets import QApplication
except ImportError:
    sys.stderr.write(
        "Ошибка: PyQt5 не найден. Установите зависимости IDE:\n"
        "    pip install -r requirements-ide.txt\n"
        "(или используйте виртуальное окружение venv/).\n"
    )
    sys.exit(1)

from ide.main_window import MainWindow
from ide.theme import apply_theme


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ZmeyGorynich IDE")
    apply_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
