from enum import Enum


class Color(str, Enum):
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    RESET_ALL = "\033[0m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"