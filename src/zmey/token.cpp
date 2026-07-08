#include "token.h"

const char* tokenTypeName(TokenType t) {
    switch (t) {
        case TokenType::NUMBER: return "NUMBER";
        case TokenType::ROOT: return "ROOT";
        case TokenType::GOYDA: return "GOYDA";
        case TokenType::BLOCK_OPEN: return "BLOCK_OPEN";
        case TokenType::BLOCK_CLOSE: return "BLOCK_CLOSE";
        case TokenType::TYPE_ANNOTATION: return "TYPE_ANNOTATION";
        case TokenType::DEF: return "DEF";
        case TokenType::RETURN_TYPE: return "RETURN_TYPE";
        case TokenType::RETURN: return "RETURN";
        case TokenType::IMPORT: return "IMPORT";
        case TokenType::AS: return "AS";
        case TokenType::DOT: return "DOT";
        case TokenType::OP: return "OP";
        case TokenType::ID: return "ID";
        case TokenType::ASSIGN: return "ASSIGN";
        case TokenType::STRING: return "STRING";
        case TokenType::NEWLINE: return "NEWLINE";
        case TokenType::COMMA: return "COMMA";
        case TokenType::BRACKET_OPEN: return "BRACKET_OPEN";
        case TokenType::BRACKET_CLOSE: return "BRACKET_CLOSE";
        case TokenType::PAREN_OPEN: return "PAREN_OPEN";
        case TokenType::PAREN_CLOSE: return "PAREN_CLOSE";
        case TokenType::EOF_TOKEN: return "EOF";
        case TokenType::INVALID: return "INVALID";
    }
    return "UNKNOWN";
}
