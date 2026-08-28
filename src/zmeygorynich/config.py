import decimal

# Глобальная точность Decimal для «плывун *» типов
decimal.getcontext().prec = 100

DEBUG = False


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)
