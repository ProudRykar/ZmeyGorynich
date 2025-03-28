import sys
from lexer import tokenize
from parser import parse
from evaluator import Context, evaluate

def run_code(filename):
    """Программа, интерпретирующая .zg в код python"""
    
    if not filename.endswith(".zg"):
        print(f"Error: {filename} is not a valid ZmeyGorynich file!")
        return

    with open(filename, 'r', encoding='utf-8') as f:
        code = f.read()

    tokens = tokenize(code)
    print("Tokens:", tokens)
    print('')

# Вывод только ошибок ZmeyGorynich при интерпретации, сейчас выводятся ошибки языка и Traceback от python 

#    try:
#        ast = parse(tokens, code)
#        print("AST:", ast)
#        print('')
#
#        context = {}
#        print('Результат программы:')
#        evaluate(ast, context)
#    except SyntaxError as e:
#
#        print(str(e))
#        sys.exit(1)

    ast = parse(tokens, code)
    print("AST:", ast)
    print('')

    context = Context()
    print('Результат программы: ')
    evaluate(ast, context)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python interpreter.py <file.zg>")
    else:
        run_code(sys.argv[1])