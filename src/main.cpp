#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include "lexer.h"
#include "parser.h"
#include "evaluator.h"
#include "context.h"
#include "builtins.h"
#include "error.h"
#include "color.h"

static void runFile(const std::string& filename) {
    std::ifstream file(filename);
    if (!file) {
        std::cerr << color::RED << "Ошибка: Не могу открыть файл: " << filename << color::RESET << "\n";
        return;
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    std::string code = buffer.str();

    try {
        Lexer lexer(code);
        auto tokens = lexer.tokenize();

        Parser parser(tokens, code);
        auto ast = parser.parse();

        Context ctx;
        registerBuiltins(ctx);

        Evaluator evaluator(&ctx, filename);
        evaluator.evaluateProgram(ast);

    } catch (const SyntaxError& e) {
        std::cerr << color::RED << "Оказия синтаксиса" << color::RESET << "\n"
                  << e.what() << "\n";
    } catch (const NameError& e) {
        std::cerr << color::RED << "Ошибка имени" << color::RESET << "\n"
                  << e.what() << "\n";
    } catch (const TypeError& e) {
        std::cerr << color::RED << "Ошибка типа" << color::RESET << "\n"
                  << e.what() << "\n";
    } catch (const ValueError& e) {
        std::cerr << color::RED << "Ошибка значения" << color::RESET << "\n"
                  << e.what() << "\n";
    } catch (const std::exception& e) {
        std::cerr << color::RED << "Ошибка" << color::RESET << "\n"
                  << e.what() << "\n";
    }
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Использование: zmeygorynych <файл.zg>\n";
        return 1;
    }

    std::string filename = argv[1];
    if (filename.size() < 3 || filename.substr(filename.size() - 3) != ".zg") {
        std::cerr << color::RED << "Ошибка: " << filename << " не является файлом Змея Горыныча!\n"
                  << color::RESET;
        return 1;
    }

    runFile(filename);
    return 0;
}
