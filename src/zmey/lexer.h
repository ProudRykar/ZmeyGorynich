#pragma once

#include "token.h"
#include <string>
#include <string_view>
#include <vector>

class Lexer {
public:
    explicit Lexer(std::string_view code);
    std::vector<Token> tokenize();

private:
    std::string_view m_code;
    size_t m_pos = 0;
    int m_line = 1;
    size_t m_line_start = 0; // byte offset of current line start

    char peek(size_t offset = 0) const;
    char advance();
    bool starts_with(const std::string& pattern, size_t pos) const;
    void skip_whitespace();
    bool skip_line_comment();
    bool skip_multiline_comment();
    bool try_match_keyword(Token& out); // multi-word keywords + operators
    Token read_number();
    Token read_string();
    Token read_identifier_or_keyword();
    Token read_symbol(); // single-char token or math operator
    Token read_next();
};
