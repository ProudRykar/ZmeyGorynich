import sys
from lexer import tokenize
from parser import parse
from evaluator import Context, evaluate

# Более удобный способ для вывода функций и дебага
DEBUG = False

def run_code(filename):
    """Программа, интерпретирующая .zg в код Python"""
    
    if not filename.endswith(".zg"):
        print(f"Error: {filename} is not a valid ZmeyGorynich file!")
        return

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            code = f.read()

        tokens = tokenize(code)
        if DEBUG:
            print("Tokens:", tokens)
            print('')

        ast = parse(tokens, code)
        if DEBUG:
            print("AST:", ast)
            print('')

        context = Context()
        print('Результат программы:')
        evaluate(ast, context, current_file=filename)

    except (SyntaxError, NameError, TypeError, ValueError, FileNotFoundError, RuntimeError) as e:
        print(f"Ошибка: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python interpreter.py <file.zg>")
    else:
        run_code(sys.argv[1])