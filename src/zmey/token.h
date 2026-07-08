#pragma once

#include <string>

enum class TokenType {
    NUMBER, ROOT, GOYDA, BLOCK_OPEN, BLOCK_CLOSE,
    TYPE_ANNOTATION, DEF, RETURN_TYPE, RETURN,
    IMPORT, AS, DOT, OP, ID, ASSIGN,
    STRING, NEWLINE, COMMA, BRACKET_OPEN, BRACKET_CLOSE,
    PAREN_OPEN, PAREN_CLOSE, EOF_TOKEN, INVALID
};

struct Token {
    TokenType type = TokenType::INVALID;
    std::string value;
    int line = 0;
    int col = 0;

    Token() = default;
    Token(TokenType t, std::string v, int l, int c)
        : type(t), value(std::move(v)), line(l), col(c) {}
};

const char* tokenTypeName(TokenType t);
