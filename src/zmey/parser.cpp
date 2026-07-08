#include "parser.h"
#include "error.h"
#include "color.h"
#include <functional>
#include <sstream>

const std::unordered_map<std::string, std::string> Parser::TYPE_MAP = {
    {"цело", "число:int"},
    {"плывун", "число:float"},
    {"строченька", "строченька"},
    {"двосуть", "двосуть"},
    {"плывун малый точный", "decimal:30"},
    {"плывун великий", "decimal:50"},
    {"плывун звездный", "decimal:100"},
    {"список цело", "list:число:int"},
    {"список плывун", "list:число:float"},
    {"список строченька", "list:строченька"},
    {"список двосуть", "list:двосуть"},
};

const std::unordered_map<std::string, int> Parser::FIXED_LOOP_MAP = {
    {"дважды", 2}, {"трижды", 3}, {"четырежды", 4},
    {"пятьжды", 5}, {"шестьжды", 6}, {"семьжды", 7},
    {"осьмьжды", 8}, {"девятьжды", 9}, {"десятьжды", 10},
    {"стожды", 100},
};

Parser::Parser(const std::vector<Token>& tokens, std::string_view code)
    : m_tokens(tokens), m_code(code) {}

const Token& Parser::cur() const {
    return m_pos < m_tokens.size() ? m_tokens[m_pos] : m_tokens.back();
}

const Token& Parser::peek(size_t offset) const {
    size_t idx = m_pos + offset;
    return idx < m_tokens.size() ? m_tokens[idx] : m_tokens.back();
}

void Parser::advance() {
    if (m_pos < m_tokens.size()) m_pos++;
}

bool Parser::accept(TokenType type) {
    if (cur().type == type) {
        advance();
        return true;
    }
    return false;
}

bool Parser::accept(TokenType type, const std::string& value) {
    if (cur().type == type && cur().value == value) {
        advance();
        return true;
    }
    return false;
}

std::string Parser::expect(TokenType type, const std::string& msg) {
    if (cur().type != type) {
        ErrorContext ctx = errorCtx();
        std::string fullMsg = msg.empty()
            ? "Ожидался токен " + std::string(tokenTypeName(type))
            : msg;
        throw SyntaxError(fullMsg, ctx);
    }
    std::string val = cur().value;
    advance();
    return val;
}

std::string Parser::expect(TokenType type, const std::string& value, const std::string& msg) {
    if (cur().type != type || cur().value != value) {
        ErrorContext ctx = errorCtx();
        std::string fullMsg = msg.empty()
            ? "Ожидался '" + value + "'"
            : msg;
        throw SyntaxError(fullMsg, ctx);
    }
    std::string val = cur().value;
    advance();
    return val;
}

ErrorContext Parser::errorCtx() const {
    ErrorContext ctx;
    ctx.line = cur().line;
    ctx.col = cur().col;
    ctx.fullCode = std::string(m_code);
    return ctx;
}

void Parser::error(const std::string& msg) const {
    throw SyntaxError(msg, errorCtx());
}

// --- Expression parsing ---

std::unique_ptr<ASTNode> Parser::parsePrimary() {
    if (m_pos >= m_tokens.size()) return nullptr;

    int line = cur().line;
    int col = cur().col;

    // String literal
    if (cur().type == TokenType::STRING) {
        auto node = std::make_unique<StringNode>();
        node->value = cur().value;
        node->line = line;
        node->col = col;
        advance();
        return node;
    }

    // Number literal
    if (cur().type == TokenType::NUMBER) {
        auto node = std::make_unique<NumberNode>();
        node->value = cur().value;
        node->line = line;
        node->col = col;
        advance();
        return node;
    }

    // RootOp: "корешок из <expr>"
    if (cur().type == TokenType::ROOT) {
        advance();
        auto expr = parseExpression();
        if (!expr) error("Ожидалось выражение после 'корешок из'");
        auto node = std::make_unique<RootOpNode>();
        node->expr = std::move(expr);
        node->line = line;
        node->col = col;
        return node;
    }

    // Array literal: [...]
    if (cur().type == TokenType::BRACKET_OPEN && cur().value == "[") {
        advance();
        auto node = std::make_unique<ArrayLiteralNode>();
        node->line = line;
        node->col = col;
        while (!(cur().type == TokenType::BRACKET_CLOSE && cur().value == "]")) {
            auto elem = parseExpression();
            if (!elem) error("Ожидалось выражение в массиве");
            node->elements.push_back(std::move(elem));
            if (cur().type == TokenType::COMMA) {
                advance();
            } else if (cur().type == TokenType::BRACKET_CLOSE && cur().value == "]") {
                break;
            } else {
                error("Ожидалась запятая или ']' в массиве");
            }
        }
        expect(TokenType::BRACKET_CLOSE, "]", "Незакрытый массив");
        return node;
    }

    // Parenthesized expression
    if (cur().type == TokenType::PAREN_OPEN && cur().value == "(") {
        advance();
        auto expr = parseExpression();
        if (!expr) error("Ожидалось выражение в скобках");
        expect(TokenType::PAREN_CLOSE, ")", "Незакрытая скобка");
        return expr;
    }

    // Identifier, Call, ArrayAccess, Bool
    if (cur().type == TokenType::ID) {
        std::string idValue = cur().value;
        int idLine = line;
        int idCol = col;

        // Bool literals
        if (idValue == "Истина") {
            advance();
            auto node = std::make_unique<BoolNode>();
            node->value = true;
            node->line = idLine;
            node->col = idCol;
            return node;
        }
        if (idValue == "Ложь") {
            advance();
            auto node = std::make_unique<BoolNode>();
            node->value = false;
            node->line = idLine;
            node->col = idCol;
            return node;
        }

        // Collect dotted identifier (e.g. "module.var")
        advance();
        while (cur().type == TokenType::DOT) {
            advance();
            if (cur().type != TokenType::ID)
                error("Ожидался идентификатор после '.'");
            idValue += "." + cur().value;
            advance();
        }

        // Check for "созвать_дружину(...)" in expression context
        if (idValue == "созвать_дружину" && cur().type == TokenType::PAREN_OPEN && cur().value == "(") {
            advance();
            auto sizeExpr = parseExpression();
            if (!sizeExpr) error("Ожидался размер массива в 'созвать_дружину'");
            expect(TokenType::COMMA, ",", "Ожидалась запятая после размера в 'созвать_дружину'");
            auto valueExpr = parseExpression();
            if (!valueExpr) error("Ожидалось значение для заполнения массива в 'созвать_дружину'");
            expect(TokenType::PAREN_CLOSE, ")", "Ожидалась ')' после аргументов в 'созвать_дружину'");
            auto node = std::make_unique<ArrayCreateNode>();
            node->size = std::move(sizeExpr);
            node->value = std::move(valueExpr);
            node->line = idLine;
            node->col = idCol;
            return node;
        }

        // Function call: ID(...)
        if (cur().type == TokenType::PAREN_OPEN && cur().value == "(") {
            advance();
            auto node = std::make_unique<CallNode>();
            node->name = idValue;
            node->line = idLine;
            node->col = idCol;
            node->args = parseCommaSeparated(
                TokenType::PAREN_CLOSE, ")",
                [this]() { return parseExpression(); },
                "Ожидалось выражение в аргументах функции");
            return node;
        }

        // Array access: ID[...]
        if (cur().type == TokenType::BRACKET_OPEN && cur().value == "[") {
            advance();
            auto index = parseExpression();
            if (!index) error("Ожидался индекс после '['");
            expect(TokenType::BRACKET_CLOSE, "]", "Ожидалась ']' после индекса");

            auto ident = std::make_unique<IdentifierNode>();
            ident->name = idValue;
            ident->line = idLine;
            ident->col = idCol;

            auto node = std::make_unique<ArrayAccessNode>();
            node->array = std::move(ident);
            node->index = std::move(index);
            node->line = idLine;
            node->col = idCol;
            return node;
        }

        // Plain identifier
        auto node = std::make_unique<IdentifierNode>();
        node->name = idValue;
        node->line = idLine;
        node->col = idCol;
        return node;
    }

    return nullptr;
}

std::unique_ptr<ASTNode> Parser::parsePower() {
    auto left = parsePrimary();
    if (!left) return nullptr;

    if (cur().type == TokenType::OP &&
        (cur().value == "**" || cur().value == "возвысить в")) {
        std::string op = cur().value;
        advance();
        auto right = parsePower();
        if (!right) error("Ожидалось выражение после '" + op + "'");

        auto node = std::make_unique<BinaryOpNode>();
        node->left = std::move(left);
        node->right = std::move(right);
        node->op = op;
        return node;
    }

    return left;
}

std::unique_ptr<ASTNode> Parser::parseMultiplicative() {
    return parseLeftAssoc(
        [this]() { return parsePower(); },
        {"*", "/", "%", "умножи на", "раздели на", "остаток от"});
}

std::unique_ptr<ASTNode> Parser::parseAdditive() {
    return parseLeftAssoc(
        [this]() { return parseMultiplicative(); },
        {"+", "-", "прибави", "отними"});
}

std::unique_ptr<ASTNode> Parser::parseComparison() {
    auto left = parseAdditive();
    if (!left) return nullptr;

    static const std::vector<std::string> comparisonOps = {
        "<", ">", "<=", ">=", "==", "!=",
        "равно", "ровно", "не равно", "неравно",
        "превосходит", "уступает",
        "ровно либо превосходит", "ровно либо уступает",
        "больше", "меньше", "меньше чем",
        "равно ли", "не равно ли", "не есть"
    };

    if (cur().type == TokenType::OP) {
        for (const auto& op : comparisonOps) {
            if (cur().value == op) {
                std::string matchOp = op;
                advance();
                auto right = parseAdditive();
                if (!right) error("Ожидалось выражение после '" + matchOp + "'");

                auto node = std::make_unique<BinaryOpNode>();
                node->left = std::move(left);
                node->right = std::move(right);
                node->op = matchOp;
                return node;
            }
        }
    }

    return left;
}

std::unique_ptr<ASTNode> Parser::parseExpression() {
    return parseComparison();
}

std::unique_ptr<ASTNode> Parser::parseLeftAssoc(
    std::function<std::unique_ptr<ASTNode>()> subparser,
    const std::vector<std::string>& ops)
{
    auto left = subparser();
    if (!left) return nullptr;

    while (cur().type == TokenType::OP) {
        bool found = false;
        for (const auto& op : ops) {
            if (cur().value == op) {
                found = true;
                break;
            }
        }
        if (!found) break;

        std::string op = cur().value;
        advance();
        auto right = subparser();
        if (!right) error("Ожидалось выражение после '" + op + "'");

        auto node = std::make_unique<BinaryOpNode>();
        node->left = std::move(left);
        node->right = std::move(right);
        node->op = op;
        left = std::move(node);
    }

    return left;
}

// --- Statement parsing ---

std::string Parser::parseTypeAnnotation() {
    if (cur().type != TokenType::TYPE_ANNOTATION) return "";
    advance();

    std::vector<std::string> parts;
    while (cur().type == TokenType::ID &&
           cur().value != "=" && cur().value != "гойда" &&
           cur().value != ")" && cur().value != ",")
    {
        parts.push_back(cur().value);
        advance();
    }

    if (parts.empty()) error("Ожидался тип после 'быти'");

    std::string typeName;
    for (size_t i = 0; i < parts.size(); ++i) {
        if (i > 0) typeName += " ";
        typeName += parts[i];
    }

    auto it = TYPE_MAP.find(typeName);
    if (it == TYPE_MAP.end())
        error("Неизвестный тип '" + typeName + "'");
    return it->second;
}

std::vector<std::unique_ptr<ASTNode>> Parser::parseCommaSeparated(
    TokenType closeType, const std::string& closeValue,
    std::function<std::unique_ptr<ASTNode>()> elementParser,
    const std::string& errorMsg)
{
    std::vector<std::unique_ptr<ASTNode>> elems;

    if (cur().type == closeType && cur().value == closeValue) {
        advance();
        return elems;
    }

    while (true) {
        auto elem = elementParser();
        if (!elem) error(errorMsg);
        elems.push_back(std::move(elem));

        if (cur().type == TokenType::COMMA) {
            advance();
            continue;
        }
        if (cur().type == closeType && cur().value == closeValue) {
            advance();
            break;
        }
        error("Ожидалась запятая или '" + closeValue + "'");
    }
    return elems;
}

std::vector<std::unique_ptr<ASTNode>> Parser::parseBlockBody() {
    std::vector<std::unique_ptr<ASTNode>> body;
    while (cur().type != TokenType::BLOCK_CLOSE) {
        auto stmt = parseStatement();
        if (stmt) {
            body.push_back(std::move(stmt));
        } else {
            error("Неожиданный токен '" + cur().value + "' в теле блока");
        }
    }
    return body;
}

std::unique_ptr<ASTNode> Parser::parseBlock() {
    auto node = std::make_unique<BlockNode>();
    node->statements = parseBlockBody();
    return node;
}

std::unique_ptr<ASTNode> Parser::parseAssignment() {
    size_t start = m_pos;
    if (cur().type != TokenType::ID) return nullptr;

    std::string varName = cur().value;
    int line = cur().line;
    int col = cur().col;
    advance();

    // Parse optional type annotation
    std::string typeHint;
    if (cur().type == TokenType::TYPE_ANNOTATION) {
        typeHint = parseTypeAnnotation();
    }

    // Array assignment: ID[expr] = expr гойда
    if (cur().type == TokenType::BRACKET_OPEN && cur().value == "[") {
        advance();
        auto index = parseExpression();
        if (!index) error("Ожидался индекс после '['");

        expect(TokenType::BRACKET_CLOSE, "]", "Ожидалась ']' после индекса");

        if (cur().type == TokenType::ASSIGN) {
            advance();
            auto expr = parseExpression();
            if (cur().type == TokenType::GOYDA) {
                advance();

                auto node = std::make_unique<ArrayAssignmentNode>();
                node->variable = varName;
                node->index = std::move(index);
                node->expr = std::move(expr);
                node->line = line;
                node->col = col;
                return node;
            }
            error("Ожидалась 'гойда' после присваивания");
        }

        // Not an array assignment — backtrack
        m_pos = start;
        return nullptr;
    }

    // Regular assignment: ID = expr гойда
    if (cur().type == TokenType::ASSIGN) {
        advance();
        auto expr = parseExpression();
        if (!expr) error("Ожидалось выражение после '='");

        if (cur().type == TokenType::GOYDA) {
            advance();

            auto node = std::make_unique<AssignmentNode>();
            node->variable = varName;
            node->expr = std::move(expr);
            node->type_hint = typeHint;
            node->line = line;
            node->col = col;
            return node;
        }
        error("Ожидалась 'гойда' после присваивания");
    }

    // No assignment — backtrack
    m_pos = start;
    return nullptr;
}

std::unique_ptr<ASTNode> Parser::parsePrint() {
    if (cur().type != TokenType::ID || cur().value != "молвить") return nullptr;

    int line = cur().line;
    int col = cur().col;
    advance();

    auto node = std::make_unique<PrintNode>();
    node->line = line;
    node->col = col;

    // Parenthesized arguments: молвить(...)
    if (cur().type == TokenType::PAREN_OPEN && cur().value == "(") {
        advance();
        node->args = parseCommaSeparated(
            TokenType::PAREN_CLOSE, ")",
            [this]() { return parseExpression(); },
            "Ожидалось выражение в 'молвить'");
    } else {
        // Single argument: молвить ID
        if (cur().type == TokenType::STRING)
            error("Строки после 'молвить' должны заключаться в ()");
        if (cur().type != TokenType::ID)
            error("Ожидалась переменная после 'молвить'");

        auto ident = std::make_unique<IdentifierNode>();
        ident->name = cur().value;
        ident->line = cur().line;
        ident->col = cur().col;
        node->args.push_back(std::move(ident));
        advance();
    }

    // Optional "и эхом затихнуть"
    if (cur().type == TokenType::ID && cur().value == "и" &&
        m_pos + 2 < m_tokens.size() &&
        peek(1).type == TokenType::ID && peek(1).value == "эхом" &&
        peek(2).type == TokenType::ID && peek(2).value == "затихнуть")
    {
        advance(); advance(); advance();
        node->silent = true;
    }

    expect(TokenType::GOYDA, "гойда", "Ожидалась 'гойда' после 'молвить'");
    return node;
}

std::unique_ptr<ASTNode> Parser::parseInput() {
    if (cur().type != TokenType::ID || cur().value != "внемли") return nullptr;

    int line = cur().line;
    int col = cur().col;
    advance();

    expect(TokenType::PAREN_OPEN, "(", "Ожидалась '(' после 'внемли'");

    auto node = std::make_unique<InputNode>();
    node->line = line;
    node->col = col;

    // Optional prompt string
    if (cur().type == TokenType::STRING) {
        auto prompt = std::make_unique<StringNode>();
        prompt->value = cur().value;
        prompt->line = cur().line;
        prompt->col = cur().col;
        node->prompt = std::move(prompt);
        advance();
        expect(TokenType::COMMA, ",", "Ожидалась запятая после строки");
    }

    if (cur().type != TokenType::ID)
        error("Ожидалась переменная");
    node->variable = cur().value;
    advance();

    expect(TokenType::PAREN_CLOSE, ")", "Ожидалась ')' после переменной");
    expect(TokenType::GOYDA, "гойда", "Ожидалась 'гойда' после 'внемли(...)'");

    return node;
}

std::unique_ptr<ASTNode> Parser::parseWhile() {
    if (cur().type != TokenType::ID || cur().value != "покуда") return nullptr;

    int line = cur().line;
    int col = cur().col;
    advance();

    auto condition = parseExpression();
    if (!condition) error("Ожидалось условие после 'покуда'");
    expect(TokenType::BLOCK_OPEN, "ухожу я в пляс", "Ожидалось 'ухожу я в пляс' после условия в 'покуда'");

    auto node = std::make_unique<WhileNode>();
    node->condition = std::move(condition);
    node->body = std::make_unique<BlockNode>();
    node->body->statements = parseBlockBody();
    node->line = line;
    node->col = col;

    expect(TokenType::BLOCK_CLOSE, "закончили пляски", "Ожидалось 'закончили пляски' после тела 'покуда'");
    return node;
}

std::unique_ptr<ASTNode> Parser::parseIf() {
    if (cur().type != TokenType::ID || cur().value != "аще") return nullptr;

    int line = cur().line;
    int col = cur().col;
    advance();

    auto condition = parseExpression();
    if (!condition) error("Ожидалось условие после 'аще'");
    expect(TokenType::ID, "то", "Ожидалось 'то' после условия");
    expect(TokenType::BLOCK_OPEN, "ухожу я в пляс", "Ожидалось 'ухожу я в пляс' после 'то'");

    auto node = std::make_unique<IfNode>();
    node->condition = std::move(condition);
    node->then_body = std::make_unique<BlockNode>();
    node->then_body->statements = parseBlockBody();
    node->elif_blocks = std::make_unique<ElifBlocksNode>();
    node->line = line;
    node->col = col;

    expect(TokenType::BLOCK_CLOSE, "закончили пляски", "Ожидалось 'закончили пляски' после тела");

    // Elif branches: "аще ли ... то ..."
    while (cur().type == TokenType::ID && cur().value == "аще") {
        advance();
        expect(TokenType::ID, "ли", "Ожидалось 'ли' после 'аще' для 'аще ли'");

        auto elifCond = parseExpression();
        if (!elifCond) error("Ожидалось условие после 'аще ли'");
        expect(TokenType::ID, "то", "Ожидалось 'то' после условия в 'аще ли'");
        expect(TokenType::BLOCK_OPEN, "ухожу я в пляс", "Ожидалось 'ухожу я в пляс' после 'то' в 'аще ли'");

        auto elifBody = std::make_unique<BlockNode>();
        elifBody->statements = parseBlockBody();

        expect(TokenType::BLOCK_CLOSE, "закончили пляски", "Ожидалось 'закончили пляски' после тела 'аще ли'");

        auto elifBranch = std::make_unique<ElifBranchNode>();
        elifBranch->condition = std::move(elifCond);
        elifBranch->body = std::move(elifBody);
        node->elif_blocks->branches.push_back(std::move(elifBranch));
    }

    // Else branch: "ино ..."
    if (cur().type == TokenType::ID && cur().value == "ино") {
        advance();
        expect(TokenType::BLOCK_OPEN, "ухожу я в пляс", "Ожидалось 'ухожу я в пляс' после 'ино'");
        node->else_body = std::make_unique<BlockNode>();
        node->else_body->statements = parseBlockBody();
        expect(TokenType::BLOCK_CLOSE, "закончили пляски", "Ожидалось 'закончили пляски' после тела 'ино'");
    }

    return node;
}

std::unique_ptr<ASTNode> Parser::parseFunctionDef() {
    if (cur().type != TokenType::DEF) return nullptr;

    int line = cur().line;
    int col = cur().col;
    advance();

    if (cur().type != TokenType::ID)
        error("Ожидалось имя функции после 'сотвори'");
    std::string funcName = cur().value;
    advance();

    expect(TokenType::PAREN_OPEN, "(", "Ожидалось '(' после имени функции");

    auto argsNode = std::make_unique<ArgsNode>();

    if (!(cur().type == TokenType::PAREN_CLOSE && cur().value == ")")) {
        while (true) {
            if (cur().type != TokenType::ID)
                error("Ожидалось имя аргумента");

            auto arg = std::make_unique<ArgNode>();
            arg->name = cur().value;
            arg->line = cur().line;
            arg->col = cur().col;
            advance();

            // Optional type annotation for arg
            if (cur().type == TokenType::TYPE_ANNOTATION && cur().value == "быти") {
                arg->type_hint = parseTypeAnnotation();
            }

            argsNode->args.push_back(std::move(arg));

            if (cur().type == TokenType::COMMA) {
                advance();
                continue;
            }
            break;
        }
    }

    expect(TokenType::PAREN_CLOSE, ")", "Ожидалось ')' после аргументов");
    expect(TokenType::RETURN_TYPE, "изречет", "Ожидалось 'изречет' после аргументов");

    // Return type
    std::vector<std::string> returnParts;
    while (cur().type == TokenType::ID &&
           cur().value != "гойда" && cur().value != "ухожу я в пляс")
    {
        returnParts.push_back(cur().value);
        advance();
    }
    if (returnParts.empty()) error("Ожидался тип возврата после 'изречет'");

    std::string returnTypeName;
    for (size_t i = 0; i < returnParts.size(); ++i) {
        if (i > 0) returnTypeName += " ";
        returnTypeName += returnParts[i];
    }
    auto it = TYPE_MAP.find(returnTypeName);
    if (it == TYPE_MAP.end())
        error("Неизвестный тип возврата '" + returnTypeName + "'");
    std::string returnType = it->second;

    expect(TokenType::BLOCK_OPEN, "ухожу я в пляс", "Ожидалось 'ухожу я в пляс' после типа возврата");

    auto node = std::make_unique<FunctionDefNode>();
    node->name = funcName;
    node->args = std::move(argsNode);
    node->body = std::make_unique<BlockNode>();
    node->body->statements = parseBlockBody();
    node->return_type = returnType;
    node->line = line;
    node->col = col;

    expect(TokenType::BLOCK_CLOSE, "закончили пляски", "Ожидалось 'закончили пляски' после тела функции");
    return node;
}

std::unique_ptr<ASTNode> Parser::parseReturn() {
    if (cur().type != TokenType::RETURN) return nullptr;

    int line = cur().line;
    int col = cur().col;
    advance();

    auto expr = parseExpression();
    if (!expr) error("Ожидалось выражение после 'возверни'");

    if (cur().type == TokenType::GOYDA)
        advance();

    auto node = std::make_unique<ReturnNode>();
    node->expr = std::move(expr);
    node->line = line;
    node->col = col;
    return node;
}

std::unique_ptr<ASTNode> Parser::parseCall() {
    if (cur().type != TokenType::ID) return nullptr;

    std::string funcName = cur().value;
    int line = cur().line;
    int col = cur().col;
    advance();

    if (!(cur().type == TokenType::PAREN_OPEN && cur().value == "(")) {
        m_pos--;
        return nullptr;
    }
    advance();

    auto node = std::make_unique<CallNode>();
    node->name = funcName;
    node->line = line;
    node->col = col;
    node->args = parseCommaSeparated(
        TokenType::PAREN_CLOSE, ")",
        [this]() { return parseExpression(); },
        "Ожидалась запятая или ')' в аргументах функции");

    if (cur().type != TokenType::GOYDA)
        error("Ожидалась 'гойда' после вызова функции");
    advance();

    return node;
}

std::unique_ptr<ASTNode> Parser::parseFixedLoop() {
    if (cur().type != TokenType::ID) return nullptr;

    auto it = FIXED_LOOP_MAP.find(cur().value);
    if (it == FIXED_LOOP_MAP.end()) return nullptr;

    int iterations = it->second;
    int line = cur().line;
    int col = cur().col;
    advance();

    auto node = std::make_unique<FixedLoopNode>();
    node->iterations = iterations;
    node->line = line;
    node->col = col;

    if (cur().type == TokenType::BLOCK_OPEN) {
        advance();
        node->body = std::make_unique<BlockNode>();
        node->body->statements = parseBlockBody();
        expect(TokenType::BLOCK_CLOSE, "закончили пляски",
               "Ожидалось 'закончили пляски' после тела '" + it->first + "'");
    } else {
        auto stmt = parseStatement();
        if (!stmt)
            error("Ожидался оператор после '" + it->first + "'");
        node->body = std::make_unique<BlockNode>();
        node->body->statements.push_back(std::move(stmt));
    }

    return node;
}

std::unique_ptr<ASTNode> Parser::parseArrayCreate() {
    if (cur().type != TokenType::ID || cur().value != "созвать_дружину") return nullptr;

    int line = cur().line;
    int col = cur().col;
    advance();

    expect(TokenType::PAREN_OPEN, "(", "Ожидалось '(' после 'созвать_дружину'");
    auto sizeExpr = parseExpression();
    if (!sizeExpr) error("Ожидался размер массива в 'созвать_дружину'");
    expect(TokenType::COMMA, ",", "Ожидалась запятая после размера в 'созвать_дружину'");
    auto valueExpr = parseExpression();
    if (!valueExpr) error("Ожидалось значение для заполнения массива в 'созвать_дружину'");
    expect(TokenType::PAREN_CLOSE, ")", "Ожидалась ')' после аргументов в 'созвать_дружину'");

    auto node = std::make_unique<ArrayCreateNode>();
    node->size = std::move(sizeExpr);
    node->value = std::move(valueExpr);
    node->line = line;
    node->col = col;
    return node;
}

std::unique_ptr<ASTNode> Parser::parseImport() {
    if (cur().type != TokenType::IMPORT) return nullptr;

    int line = cur().line;
    int col = cur().col;
    advance();

    if (cur().type != TokenType::STRING)
        error("Ожидалось имя файла в кавычках после 'прочесть книгу'");
    std::string filename = cur().value;
    // Strip quotes
    if (filename.size() >= 2 && filename.front() == '"' && filename.back() == '"')
        filename = filename.substr(1, filename.size() - 2);
    advance();

    std::string alias;
    if (cur().type == TokenType::AS) {
        advance();
        if (cur().type != TokenType::ID)
            error("Ожидался идентификатор после 'и осмыслить слова как'");
        alias = cur().value;
        advance();
    }

    if (cur().type != TokenType::GOYDA)
        error("Ожидалась 'гойда' после конструкции импорта");
    advance();

    auto node = std::make_unique<ImportNode>();
    node->filename = filename;
    node->alias = alias.empty() ? filename.substr(0, filename.find('.')) : alias;
    node->line = line;
    node->col = col;
    return node;
}

std::unique_ptr<ASTNode> Parser::parseExpressionStatement() {
    auto expr = parseExpression();
    if (!expr) return nullptr;

    if (cur().type == TokenType::GOYDA) {
        advance();

        auto node = std::make_unique<ExpressionStatementNode>();
        node->expr = std::move(expr);
        return node;
    }
    return nullptr;
}

std::unique_ptr<ASTNode> Parser::parseStatement() {
    std::unique_ptr<ASTNode> result;

    result = parseIf();
    if (result) return result;

    result = parseWhile();
    if (result) return result;

    result = parseInput();
    if (result) return result;

    result = parsePrint();
    if (result) return result;

    result = parseAssignment();
    if (result) return result;

    result = parseArrayCreate();
    if (result) return result;

    result = parseFunctionDef();
    if (result) return result;

    result = parseCall();
    if (result) return result;

    result = parseFixedLoop();
    if (result) return result;

    result = parseImport();
    if (result) return result;

    result = parseReturn();
    if (result) return result;

    result = parseExpressionStatement();
    if (result) return result;

    return nullptr;
}

std::vector<std::unique_ptr<ASTNode>> Parser::parse() {
    std::vector<std::unique_ptr<ASTNode>> ast;

    while (m_pos < m_tokens.size() && cur().type != TokenType::EOF_TOKEN) {
        auto stmt = parseStatement();
        if (stmt) {
            ast.push_back(std::move(stmt));
        } else {
            error("Неожиданный токен '" + cur().value + "'");
        }
    }

    return ast;
}
