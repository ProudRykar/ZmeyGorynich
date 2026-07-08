#include "lexer.h"
#include "error.h"
#include "utf8.h"
#include <algorithm>
#include <cctype>
#include <unordered_map>
#include <unordered_set>

Lexer::Lexer(std::string_view code) : m_code(code) {}

static int current_col(std::string_view code, size_t line_start, size_t pos) {
    return static_cast<int>(utf8::count_codepoints(
        std::string(code.substr(line_start, pos - line_start)),
        pos - line_start)) + 1;
}

char Lexer::peek(size_t offset) const {
    size_t idx = m_pos + offset;
    return idx < m_code.size() ? m_code[idx] : '\0';
}

char Lexer::advance() {
    return m_pos < m_code.size() ? m_code[m_pos++] : '\0';
}

bool Lexer::starts_with(const std::string& pattern, size_t pos) const {
    if (pos + pattern.size() > m_code.size()) return false;
    return m_code.substr(pos, pattern.size()) == pattern;
}

void Lexer::skip_whitespace() {
    while (m_pos < m_code.size()) {
        char c = m_code[m_pos];
        if (c == ' ' || c == '\t' || c == '\r') {
            m_pos++;
        } else if (c == '\n') {
            m_pos++;
            m_line++;
            m_line_start = m_pos;
        } else {
            break;
        }
    }
}

bool Lexer::skip_line_comment() {
    if (m_pos >= m_code.size() || m_code[m_pos] != '#') return false;
    while (m_pos < m_code.size() && m_code[m_pos] != '\n') {
        m_pos++;
    }
    if (m_pos < m_code.size() && m_code[m_pos] == '\n') {
        m_pos++;
        m_line++;
        m_line_start = m_pos;
    }
    return true;
}

bool Lexer::skip_multiline_comment() {
    static const std::string start_marker = "\u0413\u043E\u043B\u043E\u0441 \u043F\u0440\u0435\u0434\u043A\u043E\u0432 \u0448\u0435\u043F\u0447\u0435\u0442:"; // "Голос предков шепчет:"
    static const std::string end_marker = "\u0413\u043E\u043B\u043E\u0441 \u043F\u0440\u0435\u0434\u043A\u043E\u0432 \u0432\u043D\u0435\u0437\u0430\u043F\u043D\u043E \u0441\u0442\u0438\u0445..."; // "Голос предков внезапно стих..."

    if (!starts_with(start_marker, m_pos)) return false;

    m_pos += start_marker.size();
    size_t end_pos = m_code.find(end_marker, m_pos);
    if (end_pos == std::string_view::npos) {
        ErrorContext ctx;
        ctx.line = m_line;
        ctx.col = 1;
        throw SyntaxError("Незакрытый комментарий", ctx);
    }

    // Count newlines in the comment body
    for (size_t i = m_pos; i < end_pos; ++i) {
        if (m_code[i] == '\n') {
            m_line++;
            m_line_start = i + 1;
        }
    }

    m_pos = end_pos + end_marker.size();

    // Consume trailing newline after comment end marker
    if (m_pos < m_code.size() && m_code[m_pos] == '\n') {
        m_pos++;
        m_line++;
        m_line_start = m_pos;
    }

    return true;
}

// Multi-word patterns sorted by length descending (longest match wins)
struct KeywordEntry {
    std::string text;
    TokenType type;
};

static const KeywordEntry KEYWORD_PATTERNS[] = {
    // Multi-word (sorted by length, longest first)
    {"ровно либо превосходит", TokenType::OP},
    {"ровно либо уступает",   TokenType::OP},
    {"ухожу я в пляс",        TokenType::BLOCK_OPEN},
    {"и осмыслить слова как", TokenType::AS},
    {"закончили пляски",      TokenType::BLOCK_CLOSE},
    {"возвысить в",           TokenType::OP},
    {"прочесть книгу",        TokenType::IMPORT},
    {"умножи на",             TokenType::OP},
    {"раздели на",            TokenType::OP},
    {"остаток от",            TokenType::OP},
    {"корешок из",            TokenType::ROOT},
    {"не равно",              TokenType::OP},
    // Single-word
    {"гойда",                 TokenType::GOYDA},
    {"сотвори",               TokenType::DEF},
    {"возверни",              TokenType::RETURN},
    {"изречет",               TokenType::RETURN_TYPE},
    {"быти",                  TokenType::TYPE_ANNOTATION},
    {"прибави",               TokenType::OP},
    {"отними",                TokenType::OP},
    {"превосходит",           TokenType::OP},
    {"уступает",              TokenType::OP},
    {"ровно",                 TokenType::OP},
    {"равно",                 TokenType::OP},
    {"есть",                  TokenType::OP},
    {"отлично",               TokenType::OP},
};

bool Lexer::try_match_keyword(Token& out) {
    for (const auto& entry : KEYWORD_PATTERNS) {
        if (starts_with(entry.text, m_pos)) {
            // For multi-word patterns, verify the next character is not id_continue
            size_t next = m_pos + entry.text.size();
            if (next < m_code.size()) {
                uint32_t cp;
                size_t n = utf8::decode(m_code.data() + next, cp);
                if (n > 0 && utf8::is_id_continue(cp)) {
                    continue; // Part of a longer identifier
                }
            }
            out = Token(entry.type, entry.text, m_line, current_col(m_code, m_line_start, m_pos));
            m_pos += entry.text.size();
            return true;
        }
    }
    return false;
}

Token Lexer::read_number() {
    size_t start = m_pos;
    int col = current_col(m_code, m_line_start, m_pos);
    int line = m_line;

    // Integer part
    while (m_pos < m_code.size() && std::isdigit(static_cast<unsigned char>(m_code[m_pos]))) {
        m_pos++;
    }

    // Fractional part
    if (m_pos < m_code.size() && m_code[m_pos] == '.') {
        m_pos++;
        while (m_pos < m_code.size() && std::isdigit(static_cast<unsigned char>(m_code[m_pos]))) {
            m_pos++;
        }
    }

    // Scientific notation
    if (m_pos < m_code.size() && (m_code[m_pos] == 'e' || m_code[m_pos] == 'E')) {
        m_pos++;
        if (m_pos < m_code.size() && (m_code[m_pos] == '+' || m_code[m_pos] == '-')) {
            m_pos++;
        }
        while (m_pos < m_code.size() && std::isdigit(static_cast<unsigned char>(m_code[m_pos]))) {
            m_pos++;
        }
    }

    return Token(TokenType::NUMBER, std::string(m_code.substr(start, m_pos - start)), line, col);
}

Token Lexer::read_string() {
    int line = m_line;
    int col = current_col(m_code, m_line_start, m_pos);
    size_t start = m_pos;

    advance(); // skip opening "
    while (m_pos < m_code.size()) {
        if (m_code[m_pos] == '\\') {
            m_pos++; // skip escaped char
            if (m_pos < m_code.size()) m_pos++;
        } else if (m_code[m_pos] == '"') {
            m_pos++; // skip closing "
            return Token(TokenType::STRING,
                         std::string(m_code.substr(start, m_pos - start)), line, col);
        } else if (m_code[m_pos] == '\n') {
            break; // unterminated string
        } else {
            m_pos++;
        }
    }

    ErrorContext ctx;
    ctx.line = line;
    ctx.col = col;
    throw SyntaxError("Незакрытая строка", ctx);
}

Token Lexer::read_identifier_or_keyword() {
    size_t start = m_pos;
    int line = m_line;
    int col = current_col(m_code, m_line_start, m_pos);

    // Read the full identifier (including Cyrillic, runes, etc.)
    while (m_pos < m_code.size()) {
        uint32_t cp;
        size_t n = utf8::decode(m_code.data() + m_pos, cp);
        if (n == 0) break;
        if (!utf8::is_id_continue(cp)) break;
        m_pos += n;
    }

    std::string word(m_code.substr(start, m_pos - start));

    // Check if it's a known single-word keyword
    for (const auto& entry : KEYWORD_PATTERNS) {
        if (entry.text == word) {
            return Token(entry.type, word, line, col);
        }
    }

    return Token(TokenType::ID, word, line, col);
}

Token Lexer::read_symbol() {
    int line = m_line;
    int col = current_col(m_code, m_line_start, m_pos);
    char c = advance();

    switch (c) {
        case ',': return Token(TokenType::COMMA, ",", line, col);
        case '(': return Token(TokenType::PAREN_OPEN, "(", line, col);
        case ')': return Token(TokenType::PAREN_CLOSE, ")", line, col);
        case '[': return Token(TokenType::BRACKET_OPEN, "[", line, col);
        case ']': return Token(TokenType::BRACKET_CLOSE, "]", line, col);
        case '.': return Token(TokenType::DOT, ".", line, col);
        case '=': {
            if (peek() == '=') {
                advance();
                return Token(TokenType::OP, "==", line, col);
            }
            return Token(TokenType::ASSIGN, "=", line, col);
        }

        // Math operators and comparisons
        case '+': return Token(TokenType::OP, "+", line, col);
        case '-': return Token(TokenType::OP, "-", line, col);
        case '*': {
            if (peek() == '*') {
                advance();
                return Token(TokenType::OP, "**", line, col);
            }
            return Token(TokenType::OP, "*", line, col);
        }
        case '/': return Token(TokenType::OP, "/", line, col);
        case '%': return Token(TokenType::OP, "%", line, col);
        case '<': {
            if (peek() == '=') {
                advance();
                return Token(TokenType::OP, "<=", line, col);
            }
            return Token(TokenType::OP, "<", line, col);
        }
        case '>': {
            if (peek() == '=') {
                advance();
                return Token(TokenType::OP, ">=", line, col);
            }
            return Token(TokenType::OP, ">", line, col);
        }
        case '!': {
            if (peek() == '=') {
                advance();
                return Token(TokenType::OP, "!=", line, col);
            }
            return Token(TokenType::OP, "!", line, col);
        }
    }

    ErrorContext ctx;
    ctx.line = line;
    ctx.col = col;
    throw SyntaxError(std::string("Неизвестный символ: ") + c, ctx);
}

Token Lexer::read_next() {
    skip_whitespace();
    if (skip_multiline_comment()) return read_next();
    if (skip_line_comment()) return read_next();

    if (m_pos >= m_code.size()) {
        return Token(TokenType::EOF_TOKEN, "", m_line, 1);
    }

    char c = m_code[m_pos];

    // Try multi-word keywords first (like "ровно либо превосходит", "ухожу я в пляс", etc.)
    Token kw_token;
    if (try_match_keyword(kw_token)) {
        return kw_token;
    }

    // Number
    if (std::isdigit(static_cast<unsigned char>(c))) {
        return read_number();
    }

    // String
    if (c == '"') {
        return read_string();
    }

    // Identifier or keyword
    uint32_t cp;
    size_t n = utf8::decode(m_code.data() + m_pos, cp);
    if (n > 0 && utf8::is_id_start(cp)) {
        return read_identifier_or_keyword();
    }

    // Symbols, operators, etc.
    return read_symbol();
}

std::vector<Token> Lexer::tokenize() {
    std::vector<Token> tokens;
    while (true) {
        Token t = read_next();
        tokens.push_back(t);
        if (t.type == TokenType::EOF_TOKEN) break;
    }
    return tokens;
}
