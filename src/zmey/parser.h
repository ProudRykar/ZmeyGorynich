#pragma once

#include "ast.h"
#include "error.h"
#include "token.h"
#include <functional>
#include <memory>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

class Parser {
public:
    Parser(const std::vector<Token>& tokens, std::string_view code);
    std::vector<std::unique_ptr<ASTNode>> parse();

private:
    const std::vector<Token>& m_tokens;
    std::string_view m_code;
    size_t m_pos = 0;

    static const std::unordered_map<std::string, std::string> TYPE_MAP;
    static const std::unordered_map<std::string, int> FIXED_LOOP_MAP;

    const Token& cur() const;
    const Token& peek(size_t offset = 0) const;
    void advance();
    bool accept(TokenType type);
    bool accept(TokenType type, const std::string& value);
    std::string expect(TokenType type, const std::string& msg = "");
    std::string expect(TokenType type, const std::string& value, const std::string& msg = "");
    ErrorContext errorCtx() const;
    [[noreturn]] void error(const std::string& msg) const;

    // Expressions
    std::unique_ptr<ASTNode> parsePrimary();
    std::unique_ptr<ASTNode> parsePower();
    std::unique_ptr<ASTNode> parseMultiplicative();
    std::unique_ptr<ASTNode> parseAdditive();
    std::unique_ptr<ASTNode> parseComparison();
    std::unique_ptr<ASTNode> parseExpression();
    std::unique_ptr<ASTNode> parseLeftAssoc(
        std::function<std::unique_ptr<ASTNode>()> subparser,
        const std::vector<std::string>& ops);

    // Statements
    std::unique_ptr<ASTNode> parseStatement();
    std::unique_ptr<ASTNode> parseAssignment();
    std::unique_ptr<ASTNode> parsePrint();
    std::unique_ptr<ASTNode> parseInput();
    std::unique_ptr<ASTNode> parseWhile();
    std::unique_ptr<ASTNode> parseIf();
    std::unique_ptr<ASTNode> parseFunctionDef();
    std::unique_ptr<ASTNode> parseReturn();
    std::unique_ptr<ASTNode> parseCall();
    std::unique_ptr<ASTNode> parseFixedLoop();
    std::unique_ptr<ASTNode> parseArrayCreate();
    std::unique_ptr<ASTNode> parseImport();
    std::unique_ptr<ASTNode> parseExpressionStatement();

    // Helpers
    std::string parseTypeAnnotation();
    std::vector<std::unique_ptr<ASTNode>> parseCommaSeparated(
        TokenType closeType, const std::string& closeValue,
        std::function<std::unique_ptr<ASTNode>()> elementParser,
        const std::string& errorMsg);
    std::vector<std::unique_ptr<ASTNode>> parseBlockBody();
    std::unique_ptr<ASTNode> parseBlock();
};
