#include <catch2/catch_test_macros.hpp>
#include "lexer.h"
#include "parser.h"
#include "error.h"
#include <vector>

static std::vector<Token> tok(const std::string& code) {
    Lexer lexer(code);
    return lexer.tokenize();
}

static std::vector<std::unique_ptr<ASTNode>> parse(const std::string& code) {
    auto tokens = tok(code);
    Parser parser(tokens, code);
    return parser.parse();
}

TEST_CASE("Parser assignment", "[parser]") {
    SECTION("simple assignment") {
        auto ast = parse("x = 42 гойда");
        REQUIRE(ast.size() == 1);
        auto* assign = dynamic_cast<AssignmentNode*>(ast[0].get());
        REQUIRE(assign != nullptr);
        CHECK(assign->variable == "x");
        CHECK(assign->type_hint.empty());
        REQUIRE(assign->expr != nullptr);
        CHECK(assign->expr->getType() == NodeType::Number);
    }

    SECTION("typed assignment") {
        auto ast = parse("x быти цело = 42 гойда");
        REQUIRE(ast.size() == 1);
        auto* assign = dynamic_cast<AssignmentNode*>(ast[0].get());
        REQUIRE(assign != nullptr);
        CHECK(assign->variable == "x");
        CHECK(assign->type_hint == "число:int");
    }

    SECTION("float assignment") {
        auto ast = parse("y быти плывун = 3.14 гойда");
        REQUIRE(ast.size() == 1);
        auto* assign = dynamic_cast<AssignmentNode*>(ast[0].get());
        REQUIRE(assign != nullptr);
        CHECK(assign->variable == "y");
        CHECK(assign->type_hint == "число:float");
    }
}

TEST_CASE("Parser print", "[parser]") {
    SECTION("print with parens") {
        auto ast = parse("молвить(42) гойда");
        REQUIRE(ast.size() == 1);
        auto* print = dynamic_cast<PrintNode*>(ast[0].get());
        REQUIRE(print != nullptr);
        REQUIRE(print->args.size() == 1);
        CHECK(print->args[0]->getType() == NodeType::Number);
        CHECK(print->silent == false);
    }

    SECTION("print multiple args") {
        auto ast = parse("молвить(1, 2, 3) гойда");
        REQUIRE(ast.size() == 1);
        auto* print = dynamic_cast<PrintNode*>(ast[0].get());
        REQUIRE(print != nullptr);
        REQUIRE(print->args.size() == 3);
    }

    SECTION("print with silence") {
        auto ast = parse("молвить(42) и эхом затихнуть гойда");
        REQUIRE(ast.size() == 1);
        auto* print = dynamic_cast<PrintNode*>(ast[0].get());
        REQUIRE(print != nullptr);
        CHECK(print->silent == true);
    }

    SECTION("print with variable") {
        auto ast = parse("молвить x гойда");
        REQUIRE(ast.size() == 1);
        auto* print = dynamic_cast<PrintNode*>(ast[0].get());
        REQUIRE(print != nullptr);
        REQUIRE(print->args.size() == 1);
        CHECK(print->args[0]->getType() == NodeType::Identifier);
        auto* ident = dynamic_cast<IdentifierNode*>(print->args[0].get());
        REQUIRE(ident != nullptr);
        CHECK(ident->name == "x");
    }
}

TEST_CASE("Parser function call", "[parser]") {
    SECTION("simple call") {
        auto ast = parse("добавить(1, 2) гойда");
        REQUIRE(ast.size() == 1);
        auto* call = dynamic_cast<CallNode*>(ast[0].get());
        REQUIRE(call != nullptr);
        CHECK(call->name == "добавить");
        REQUIRE(call->args.size() == 2);
    }

    SECTION("call no args") {
        auto ast = parse("функция() гойда");
        REQUIRE(ast.size() == 1);
        auto* call = dynamic_cast<CallNode*>(ast[0].get());
        REQUIRE(call != nullptr);
        CHECK(call->name == "функция");
        CHECK(call->args.empty());
    }
}

TEST_CASE("Parser if statement", "[parser]") {
    SECTION("simple if") {
        auto ast = parse("аще x > 0 то ухожу я в пляс молвить(42) гойда закончили пляски");
        REQUIRE(ast.size() == 1);
        auto* ifNode = dynamic_cast<IfNode*>(ast[0].get());
        REQUIRE(ifNode != nullptr);
        REQUIRE(ifNode->condition != nullptr);
        CHECK(ifNode->condition->getType() == NodeType::BinaryOp);
        REQUIRE(ifNode->then_body != nullptr);
        CHECK(ifNode->then_body->statements.size() == 1);
        CHECK(ifNode->elif_blocks->branches.empty());
        CHECK(ifNode->else_body == nullptr);
    }

    SECTION("if-else") {
        auto ast = parse(
            "аще x > 0 то ухожу я в пляс молвить(1) гойда закончили пляски "
            "ино ухожу я в пляс молвить(2) гойда закончили пляски");
        REQUIRE(ast.size() == 1);
        auto* ifNode = dynamic_cast<IfNode*>(ast[0].get());
        REQUIRE(ifNode != nullptr);
        REQUIRE(ifNode->else_body != nullptr);
        CHECK(ifNode->else_body->statements.size() == 1);
    }
}

TEST_CASE("Parser while loop", "[parser]") {
    auto ast = parse("покуда x < 10 ухожу я в пляс x = x + 1 гойда закончили пляски");
    REQUIRE(ast.size() == 1);
    auto* whileNode = dynamic_cast<WhileNode*>(ast[0].get());
    REQUIRE(whileNode != nullptr);
    REQUIRE(whileNode->condition != nullptr);
    CHECK(whileNode->condition->getType() == NodeType::BinaryOp);
    REQUIRE(whileNode->body != nullptr);
    CHECK(whileNode->body->statements.size() == 1);
}

TEST_CASE("Parser function definition", "[parser]") {
    auto ast = parse(
        "сотвори добавить(x быти цело, y быти цело) изречет цело "
        "ухожу я в пляс возверни x + y гойда закончили пляски");
    REQUIRE(ast.size() == 1);
    auto* func = dynamic_cast<FunctionDefNode*>(ast[0].get());
    REQUIRE(func != nullptr);
    CHECK(func->name == "добавить");
    CHECK(func->return_type == "число:int");
    REQUIRE(func->args != nullptr);
    REQUIRE(func->args->args.size() == 2);
    CHECK(func->args->args[0]->name == "x");
    CHECK(func->args->args[0]->type_hint == "число:int");
    CHECK(func->args->args[1]->name == "y");
    REQUIRE(func->body != nullptr);
    CHECK(func->body->statements.size() == 1);
}

TEST_CASE("Parser return", "[parser]") {
    auto ast = parse("возверни 42 гойда");
    REQUIRE(ast.size() == 1);
    auto* ret = dynamic_cast<ReturnNode*>(ast[0].get());
    REQUIRE(ret != nullptr);
    REQUIRE(ret->expr != nullptr);
    CHECK(ret->expr->getType() == NodeType::Number);
}

TEST_CASE("Parser fixed loop", "[parser]") {
    SECTION("with block") {
        auto ast = parse("дважды ухожу я в пляс молвить(1) гойда закончили пляски");
        REQUIRE(ast.size() == 1);
        auto* loop = dynamic_cast<FixedLoopNode*>(ast[0].get());
        REQUIRE(loop != nullptr);
        CHECK(loop->iterations == 2);
    }

    SECTION("without block") {
        auto ast = parse("трижды молвить(1) гойда");
        REQUIRE(ast.size() == 1);
        auto* loop = dynamic_cast<FixedLoopNode*>(ast[0].get());
        REQUIRE(loop != nullptr);
        CHECK(loop->iterations == 3);
    }
}

TEST_CASE("Parser import", "[parser]") {
    auto ast = parse("прочесть книгу \"test.zg\" гойда");
    REQUIRE(ast.size() == 1);
    auto* imp = dynamic_cast<ImportNode*>(ast[0].get());
    REQUIRE(imp != nullptr);
    CHECK(imp->filename == "test.zg");
    CHECK(!imp->alias.empty());
}

TEST_CASE("Parser expressions", "[parser]") {
    SECTION("binary operation") {
        auto ast = parse("x = 1 + 2 гойда");
        REQUIRE(ast.size() == 1);
        auto* assign = dynamic_cast<AssignmentNode*>(ast[0].get());
        REQUIRE(assign != nullptr);
        REQUIRE(assign->expr != nullptr);
        CHECK(assign->expr->getType() == NodeType::BinaryOp);
        auto* binop = dynamic_cast<BinaryOpNode*>(assign->expr.get());
        REQUIRE(binop != nullptr);
        CHECK(binop->op == "+");
    }

    SECTION("comparison") {
        auto ast = parse("x = 5 > 3 гойда");
        REQUIRE(ast.size() == 1);
        auto* assign = dynamic_cast<AssignmentNode*>(ast[0].get());
        REQUIRE(assign != nullptr);
        auto* binop = dynamic_cast<BinaryOpNode*>(assign->expr.get());
        REQUIRE(binop != nullptr);
        CHECK(binop->op == ">");
    }

    SECTION("slavic operator") {
        auto ast = parse("x = 1 прибави 2 гойда");
        REQUIRE(ast.size() == 1);
        auto* assign = dynamic_cast<AssignmentNode*>(ast[0].get());
        REQUIRE(assign != nullptr);
        auto* binop = dynamic_cast<BinaryOpNode*>(assign->expr.get());
        REQUIRE(binop != nullptr);
        CHECK(binop->op == "прибави");
    }
}

TEST_CASE("Parser invalid syntax", "[parser]") {
    SECTION("missing гойда") {
        auto tokens = tok("x = 42");
        Parser parser(tokens, "x = 42");
        CHECK_THROWS_AS(parser.parse(), SyntaxError);
    }

    SECTION("unknown token") {
        CHECK_THROWS_AS(tok("x = @ гойда"), SyntaxError);
    }
}

TEST_CASE("Parser input", "[parser]") {
    SECTION("input with prompt") {
        auto ast = parse("внемли(\"введите x\", x) гойда");
        REQUIRE(ast.size() == 1);
        auto* input = dynamic_cast<InputNode*>(ast[0].get());
        REQUIRE(input != nullptr);
        REQUIRE(input->prompt != nullptr);
        CHECK(input->variable == "x");
    }

    SECTION("input without prompt") {
        auto ast = parse("внемли(x) гойда");
        REQUIRE(ast.size() == 1);
        auto* input = dynamic_cast<InputNode*>(ast[0].get());
        REQUIRE(input != nullptr);
        CHECK(input->prompt == nullptr);
        CHECK(input->variable == "x");
    }
}
