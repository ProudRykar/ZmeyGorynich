#include <catch2/catch_test_macros.hpp>
#include "lexer.h"
#include <vector>

static std::vector<Token> tok(const std::string& code) {
    Lexer lexer(code);
    return lexer.tokenize();
}

static TokenType tt(const std::string& code, int index) {
    auto tokens = tok(code);
    if (index < static_cast<int>(tokens.size())) {
        return tokens[index].type;
    }
    return TokenType::INVALID;
}

static std::string tv(const std::string& code, int index) {
    auto tokens = tok(code);
    if (index < static_cast<int>(tokens.size())) {
        return tokens[index].value;
    }
    return "";
}

#define CHECK_TOKEN(code, idx, expected_type, expected_value) \
    do { \
        auto toks = tok(code); \
        REQUIRE(idx < static_cast<int>(toks.size())); \
        CHECK(toks[idx].type == expected_type); \
        CHECK(toks[idx].value == expected_value); \
    } while(0)

TEST_CASE("Lexer basics", "[lexer]") {
    SECTION("simple assignment") {
        // x = 42 гойда
        auto tokens = tok("x = 42 гойда");
        REQUIRE(tokens.size() == 5);
        CHECK(tokens[0].type == TokenType::ID);
        CHECK(tokens[0].value == "x");
        CHECK(tokens[1].type == TokenType::ASSIGN);
        CHECK(tokens[1].value == "=");
        CHECK(tokens[2].type == TokenType::NUMBER);
        CHECK(tokens[2].value == "42");
        CHECK(tokens[3].type == TokenType::GOYDA);
        CHECK(tokens[3].value == "гойда");
        CHECK(tokens[4].type == TokenType::EOF_TOKEN);
    }

    SECTION("string token") {
        auto tokens = tok("\"привет\" гойда");
        CHECK(tokens[0].type == TokenType::STRING);
        CHECK(tokens[0].value == "\"привет\"");
        CHECK(tokens[1].type == TokenType::GOYDA);
    }

    SECTION("function call") {
        auto tokens = tok("молвить(x) гойда");
        CHECK(tokens[0].type == TokenType::ID);
        CHECK(tokens[0].value == "молвить");
        CHECK(tokens[1].type == TokenType::PAREN_OPEN);
        CHECK(tokens[2].type == TokenType::ID);
        CHECK(tokens[2].value == "x");
        CHECK(tokens[3].type == TokenType::PAREN_CLOSE);
        CHECK(tokens[4].type == TokenType::GOYDA);
    }

    SECTION("line comment") {
        auto tokens = tok("# Это комментарий\nx = 42 гойда");
        CHECK(tokens[0].type == TokenType::ID);
        CHECK(tokens[0].value == "x");
    }

    SECTION("multi-line comment") {
        auto tokens = tok("Голос предков шепчет: текст\nГолос предков внезапно стих...\nx = 42 гойда");
        CHECK(tokens[0].type == TokenType::ID);
        CHECK(tokens[0].value == "x");
    }
}

TEST_CASE("Lexer operators", "[lexer]") {
    SECTION("comparison operators") {
        CHECK_TOKEN("x < 5 гойда", 1, TokenType::OP, "<");
        CHECK_TOKEN("x > 5 гойда", 1, TokenType::OP, ">");
        CHECK_TOKEN("x <= 5 гойда", 1, TokenType::OP, "<=");
        CHECK_TOKEN("x >= 5 гойда", 1, TokenType::OP, ">=");
        CHECK_TOKEN("x == 5 гойда", 1, TokenType::OP, "==");
        CHECK_TOKEN("x != 5 гойда", 1, TokenType::OP, "!=");
    }

    SECTION("math operators") {
        CHECK_TOKEN("x + y гойда", 1, TokenType::OP, "+");
        CHECK_TOKEN("x - y гойда", 1, TokenType::OP, "-");
        CHECK_TOKEN("x * y гойда", 1, TokenType::OP, "*");
        CHECK_TOKEN("x / y гойда", 1, TokenType::OP, "/");
        CHECK_TOKEN("x % y гойда", 1, TokenType::OP, "%");
        CHECK_TOKEN("x ** y гойда", 1, TokenType::OP, "**");
    }

    SECTION("slavic operators") {
        CHECK_TOKEN("прибави", 0, TokenType::OP, "прибави");
        CHECK_TOKEN("отними", 0, TokenType::OP, "отними");
        CHECK_TOKEN("умножи на", 0, TokenType::OP, "умножи на");
        CHECK_TOKEN("раздели на", 0, TokenType::OP, "раздели на");
        CHECK_TOKEN("остаток от", 0, TokenType::OP, "остаток от");
        CHECK_TOKEN("ровно либо превосходит", 0, TokenType::OP, "ровно либо превосходит");
        CHECK_TOKEN("ровно либо уступает", 0, TokenType::OP, "ровно либо уступает");
        CHECK_TOKEN("превосходит", 0, TokenType::OP, "превосходит");
        CHECK_TOKEN("уступает", 0, TokenType::OP, "уступает");
        CHECK_TOKEN("ровно", 0, TokenType::OP, "ровно");
        CHECK_TOKEN("равно", 0, TokenType::OP, "равно");
        CHECK_TOKEN("есть", 0, TokenType::OP, "есть");
        CHECK_TOKEN("отлично", 0, TokenType::OP, "отлично");
        CHECK_TOKEN("не равно", 0, TokenType::OP, "не равно");
    }
}

TEST_CASE("Lexer keywords", "[lexer]") {
    CHECK_TOKEN("гойда", 0, TokenType::GOYDA, "гойда");
    CHECK_TOKEN("сотвори", 0, TokenType::DEF, "сотвори");
    CHECK_TOKEN("возверни", 0, TokenType::RETURN, "возверни");
    CHECK_TOKEN("изречет", 0, TokenType::RETURN_TYPE, "изречет");
    CHECK_TOKEN("быти", 0, TokenType::TYPE_ANNOTATION, "быти");
    CHECK_TOKEN("корешок из", 0, TokenType::ROOT, "корешок из");
    CHECK_TOKEN("прочесть книгу", 0, TokenType::IMPORT, "прочесть книгу");
    CHECK_TOKEN("ухожу я в пляс", 0, TokenType::BLOCK_OPEN, "ухожу я в пляс");
    CHECK_TOKEN("закончили пляски", 0, TokenType::BLOCK_CLOSE, "закончили пляски");
    CHECK_TOKEN("и осмыслить слова как", 0, TokenType::AS, "и осмыслить слова как");
}

TEST_CASE("Lexer numbers", "[lexer]") {
    CHECK_TOKEN("42 гойда", 0, TokenType::NUMBER, "42");
    CHECK_TOKEN("3.14 гойда", 0, TokenType::NUMBER, "3.14");
    CHECK_TOKEN("1e10 гойда", 0, TokenType::NUMBER, "1e10");
    CHECK_TOKEN("1.5e-3 гойда", 0, TokenType::NUMBER, "1.5e-3");
}

TEST_CASE("Lexer boolean identifiers", "[lexer]") {
    // истина/ложь are plain IDs in the lexer; the parser handles them
    auto tokens = tok("x = истина гойда");
    CHECK(tokens[0].type == TokenType::ID);
    CHECK(tokens[0].value == "x");
    CHECK(tokens[1].type == TokenType::ASSIGN);
    CHECK(tokens[2].type == TokenType::ID);
    CHECK(tokens[2].value == "истина");
    CHECK(tokens[3].type == TokenType::GOYDA);
}

TEST_CASE("Lexer line and column", "[lexer]") {
    auto tokens = tok("x = 42 гойда");
    CHECK(tokens[0].line == 1);
    CHECK(tokens[0].col == 1);
    CHECK(tokens[1].col == 3);
    CHECK(tokens[2].col == 5);
    CHECK(tokens[3].col == 8);
}

TEST_CASE("Lexer multi-line", "[lexer]") {
    auto tokens = tok("x = 1 гойда\ny = 2 гойда");
    CHECK(tokens[0].type == TokenType::ID);
    CHECK(tokens[4].type == TokenType::ID);
    CHECK(tokens[4].value == "y");
    CHECK(tokens[4].line == 2);
}
