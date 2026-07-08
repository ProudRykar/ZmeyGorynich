#include <catch2/catch_test_macros.hpp>
#include "lexer.h"
#include "parser.h"
#include "evaluator.h"
#include "context.h"
#include "error.h"
#include "value.h"
#include "builtins.h"
#include <sstream>
#include <iostream>

static std::vector<Token> tok(const std::string& code) {
    Lexer lexer(code);
    return lexer.tokenize();
}

static std::vector<std::unique_ptr<ASTNode>> parse(const std::string& code) {
    auto tokens = tok(code);
    Parser parser(tokens, code);
    return parser.parse();
}

struct Capture {
    std::streambuf* old;
    std::ostringstream ss;
    Capture() : old(std::cout.rdbuf(ss.rdbuf())) {}
    ~Capture() { std::cout.rdbuf(old); }
    std::string str() { return ss.str(); }
};

static void eval(const std::string& code, Context& ctx) {
    registerBuiltins(ctx);
    auto ast = parse(code);
    Evaluator ev(&ctx);
    ev.evaluateProgram(ast);
}

static Context makeContext() {
    Context ctx;
    registerBuiltins(ctx);
    return ctx;
}

static void eval(const std::string& code) {
    Context ctx = makeContext();
    eval(code, ctx);
}

TEST_CASE("Evaluator assignment", "[evaluator]") {
    Context ctx;

    SECTION("simple assignment") {
        eval("x = 42 гойда", ctx);
        REQUIRE(ctx.hasVariable("x"));
        CHECK(ctx.get("x").getInt() == 42);
    }

    SECTION("typed int assignment") {
        eval("x быти цело = 42 гойда", ctx);
        REQUIRE(ctx.hasVariable("x"));
        CHECK(ctx.get("x").getInt() == 42);
        CHECK(ctx.getTypeHint("x") == "число:int");
    }

    SECTION("typed float assignment") {
        eval("x быти плывун = 3.14 гойда", ctx);
        REQUIRE(ctx.hasVariable("x"));
        CHECK(ctx.get("x").getFloat() == 3.14);
        CHECK(ctx.getTypeHint("x") == "число:float");
    }

    SECTION("typed string assignment") {
        eval("x быти строченька = \"привет\" гойда", ctx);
        REQUIRE(ctx.hasVariable("x"));
        CHECK(ctx.get("x").getString() == "привет");
        CHECK(ctx.getTypeHint("x") == "строченька");
    }

    SECTION("typed bool assignment") {
        Context ctx;
        eval("x быти двосуть = Истина гойда", ctx);
        REQUIRE(ctx.hasVariable("x"));
        CHECK(ctx.get("x").getBool() == true);
    }

    SECTION("string assignment") {
        eval("x = \"hello\" гойда", ctx);
        REQUIRE(ctx.hasVariable("x"));
        CHECK(ctx.get("x").getString() == "hello");
    }

    SECTION("float assignment") {
        eval("x = 3.14 гойда", ctx);
        REQUIRE(ctx.hasVariable("x"));
        CHECK(ctx.get("x").getFloat() == 3.14);
    }

    SECTION("bool assignment") {
        Context ctx;
        eval("x = Истина гойда", ctx);
        REQUIRE(ctx.hasVariable("x"));
        CHECK(ctx.get("x").getBool() == true);
    }



    SECTION("bool false assignment") {
        eval("x = Ложь гойда", ctx);
        REQUIRE(ctx.hasVariable("x"));
        CHECK(ctx.get("x").getBool() == false);
    }

    SECTION("multiple assignments") {
        eval("x = 1 гойда y = 2 гойда z = 3 гойда", ctx);
        CHECK(ctx.get("x").getInt() == 1);
        CHECK(ctx.get("y").getInt() == 2);
        CHECK(ctx.get("z").getInt() == 3);
    }

    SECTION("reassign variable") {
        eval("x = 1 гойда x = 2 гойда", ctx);
        CHECK(ctx.get("x").getInt() == 2);
    }
}

TEST_CASE("Evaluator print", "[evaluator]") {
    SECTION("print number") {
        Context ctx;
        Capture cap;
        eval("молвить(42) гойда", ctx);
        CHECK(cap.str() == "42");
    }

    SECTION("print string") {
        Context ctx;
        Capture cap;
        eval("молвить(\"hello\") гойда", ctx);
        CHECK(cap.str() == "hello");
    }

    SECTION("print multiple args") {
        Context ctx;
        Capture cap;
        eval("молвить(1, 2, 3) гойда", ctx);
        CHECK(cap.str() == "123");
    }

    SECTION("print silent") {
        Context ctx;
        Capture cap;
        eval("молвить(\"test\") и эхом затихнуть гойда", ctx);
        CHECK(cap.str() == "test\n");
    }

    SECTION("print variable") {
        Context ctx;
        Capture cap;
        eval("x = 99 гойда молвить(x) гойда", ctx);
        CHECK(cap.str() == "99");
    }
}

TEST_CASE("Evaluator binary operations", "[evaluator]") {
    SECTION("addition") {
        Context ctx;
        eval("x = 1 + 2 гойда", ctx);
        CHECK(ctx.get("x").getInt() == 3);
    }

    SECTION("subtraction") {
        Context ctx;
        eval("x = 10 - 3 гойда", ctx);
        CHECK(ctx.get("x").getInt() == 7);
    }

    SECTION("multiplication") {
        Context ctx;
        eval("x = 4 * 5 гойда", ctx);
        CHECK(ctx.get("x").getInt() == 20);
    }

    SECTION("division") {
        Context ctx;
        eval("x = 10 / 3 гойда", ctx);
        CHECK(std::abs(ctx.get("x").getFloat() - 3.33333) < 0.001);
    }

    SECTION("modulo") {
        Context ctx;
        eval("x = 10 % 3 гойда", ctx);
        CHECK(ctx.get("x").getInt() == 1);
    }

    SECTION("exponentiation") {
        Context ctx;
        eval("x = 2 ** 3 гойда", ctx);
        CHECK(ctx.get("x").getInt() == 8);
    }

    SECTION("greater than") {
        Context ctx;
        eval("x = 5 > 3 гойда y = 3 > 5 гойда", ctx);
        CHECK(ctx.get("x").getBool() == true);
        CHECK(ctx.get("y").getBool() == false);
    }

    SECTION("less than") {
        Context ctx;
        eval("x = 3 < 5 гойда y = 5 < 3 гойда", ctx);
        CHECK(ctx.get("x").getBool() == true);
        CHECK(ctx.get("y").getBool() == false);
    }

    SECTION("equal") {
        Context ctx;
        eval("x = 5 == 5 гойда y = 5 == 3 гойда", ctx);
        CHECK(ctx.get("x").getBool() == true);
        CHECK(ctx.get("y").getBool() == false);
    }

    SECTION("not equal") {
        Context ctx;
        eval("x = 5 != 3 гойда y = 5 != 5 гойда", ctx);
        CHECK(ctx.get("x").getBool() == true);
        CHECK(ctx.get("y").getBool() == false);
    }

    SECTION("greater or equal") {
        Context ctx;
        eval("x = 5 >= 5 гойда y = 5 >= 3 гойда z = 3 >= 5 гойда", ctx);
        CHECK(ctx.get("x").getBool() == true);
        CHECK(ctx.get("y").getBool() == true);
        CHECK(ctx.get("z").getBool() == false);
    }

    SECTION("less or equal") {
        Context ctx;
        eval("x = 5 <= 5 гойда y = 3 <= 5 гойда z = 5 <= 3 гойда", ctx);
        CHECK(ctx.get("x").getBool() == true);
        CHECK(ctx.get("y").getBool() == true);
        CHECK(ctx.get("z").getBool() == false);
    }

    SECTION("string concat") {
        Context ctx;
        eval("x = \"hello\" + \" world\" гойда", ctx);
        CHECK(ctx.get("x").getString() == "hello world");
    }

    SECTION("slavic operator прибави") {
        Context ctx;
        eval("x = 10 прибави 5 гойда", ctx);
        CHECK(ctx.get("x").getInt() == 15);
    }

    SECTION("slavic operator отними") {
        Context ctx;
        eval("x = 10 отними 5 гойда", ctx);
        CHECK(ctx.get("x").getInt() == 5);
    }

    SECTION("slavic operator ровно") {
        Context ctx;
        eval("x = 5 ровно 5 гойда y = 5 ровно 3 гойда", ctx);
        CHECK(ctx.get("x").getBool() == true);
        CHECK(ctx.get("y").getBool() == false);
    }

    SECTION("slavic operator превосходит") {
        Context ctx;
        eval("x = 5 превосходит 3 гойда", ctx);
        CHECK(ctx.get("x").getBool() == true);
    }
}

TEST_CASE("Evaluator sqrt", "[evaluator]") {
    SECTION("integer sqrt") {
        Context ctx;
        eval("x = корешок из 9 гойда", ctx);
        CHECK(ctx.get("x").getInt() == 3);
    }

    SECTION("non-perfect sqrt") {
        Context ctx;
        eval("x = корешок из 2 гойда", ctx);
        CHECK(ctx.get("x").getType() == Value::Type::Float);
    }
}

TEST_CASE("Evaluator if statement", "[evaluator]") {
    SECTION("if true") {
        Context ctx;
        Capture cap;
        eval("x = 5 гойда аще x > 0 то ухожу я в пляс молвить(\"yes\") гойда закончили пляски", ctx);
        CHECK(cap.str() == "yes");
    }

    SECTION("if false") {
        Context ctx;
        Capture cap;
        eval("x = 0 гойда аще x > 0 то ухожу я в пляс молвить(\"yes\") гойда закончили пляски", ctx);
        CHECK(cap.str().empty());
    }

    SECTION("if-else") {
        Context ctx;
        Capture cap;
        eval("x = 0 гойда x = x - 1 гойда аще x > 0 то ухожу я в пляс молвить(\"pos\") гойда закончили пляски ино ухожу я в пляс молвить(\"neg\") гойда закончили пляски", ctx);
        CHECK(cap.str() == "neg");
    }

    SECTION("if-elif-else") {
        Context ctx;
        Capture cap;
        eval("x = 0 гойда аще x > 0 то ухожу я в пляс молвить(\"pos\") гойда закончили пляски аще ли x < 0 то ухожу я в пляс молвить(\"neg\") гойда закончили пляски ино ухожу я в пляс молвить(\"zero\") гойда закончили пляски", ctx);
        CHECK(cap.str() == "zero");
    }

    SECTION("if-elif true") {
        Context ctx;
        Capture cap;
        eval("x = 5 гойда аще x > 10 то ухожу я в пляс молвить(\"big\") гойда закончили пляски аще ли x > 0 то ухожу я в пляс молвить(\"small\") гойда закончили пляски", ctx);
        CHECK(cap.str() == "small");
    }
}

TEST_CASE("Evaluator while loop", "[evaluator]") {
    SECTION("basic while") {
        Context ctx;
        eval("x = 0 гойда покуда x < 3 ухожу я в пляс x = x + 1 гойда закончили пляски", ctx);
        CHECK(ctx.get("x").getInt() == 3);
    }

    SECTION("while zero iterations") {
        Context ctx;
        eval("x = 5 гойда покуда x < 3 ухожу я в пляс x = x + 1 гойда закончили пляски", ctx);
        CHECK(ctx.get("x").getInt() == 5);
    }
}

TEST_CASE("Evaluator fixed loop", "[evaluator]") {
    SECTION("дважды") {
        Context ctx;
        eval("x = 0 гойда дважды ухожу я в пляс x = x + 1 гойда закончили пляски", ctx);
        CHECK(ctx.get("x").getInt() == 2);
    }

    SECTION("трижды") {
        Context ctx;
        eval("x = 0 гойда трижды x = x + 1 гойда", ctx);
        CHECK(ctx.get("x").getInt() == 3);
    }
}

TEST_CASE("Evaluator function", "[evaluator]") {
    SECTION("define and call") {
        Context ctx;
        eval("сотвори удвоить(x быти цело) изречет цело ухожу я в пляс возверни x * 2 гойда закончили пляски y = удвоить(5) гойда", ctx);
        REQUIRE(ctx.hasVariable("y"));
        CHECK(ctx.get("y").getInt() == 10);
    }

    SECTION("function with no args") {
        Context ctx;
        eval("сотвори пять() изречет цело ухожу я в пляс возверни 5 гойда закончили пляски y = пять() гойда", ctx);
        CHECK(ctx.get("y").getInt() == 5);
    }

    SECTION("function with multiple args") {
        Context ctx;
        eval("сотвори сумма(a быти цело, b быти цело) изречет цело ухожу я в пляс возверни a + b гойда закончили пляски y = сумма(3, 4) гойда", ctx);
        CHECK(ctx.get("y").getInt() == 7);
    }

    SECTION("function with side effect on outer scope") {
        Context ctx;
        eval("x = 0 гойда сотвори increment(val быти цело) изречет цело ухожу я в пляс возверни val + 1 гойда закончили пляски y = increment(5) гойда", ctx);
        CHECK(ctx.get("y").getInt() == 6);
    }
}

TEST_CASE("Evaluator type errors", "[evaluator]") {
    SECTION("string assigned to int") {
        Context ctx;
        CHECK_THROWS_AS(eval("x быти цело = \"hello\" гойда", ctx), TypeError);
    }

    SECTION("int assigned to string") {
        Context ctx;
        eval("x быти строченька = 42 гойда", ctx);
        CHECK(ctx.get("x").getString() == "42");
        CHECK(ctx.getTypeHint("x") == "строченька");
    }

    SECTION("float assigned to int") {
        Context ctx;
        eval("x быти цело = 3.14 гойда", ctx);
        CHECK(ctx.get("x").getInt() == 3);
        CHECK(ctx.getTypeHint("x") == "число:int");
    }

    SECTION("undefined variable") {
        Context ctx;
        CHECK_THROWS_AS(eval("x = y + 1 гойда", ctx), NameError);
    }

    SECTION("undefined function") {
        Context ctx;
        CHECK_THROWS_AS(eval("несуществующая() гойда", ctx), NameError);
    }

    SECTION("divide by zero") {
        Context ctx;
        CHECK_THROWS_AS(eval("x = 1 / 0 гойда", ctx), ValueError);
    }
}

TEST_CASE("Evaluator arrays", "[evaluator]") {
    SECTION("array literal") {
        Context ctx;
        eval("x = [1, 2, 3] гойда", ctx);
        REQUIRE(ctx.get("x").getType() == Value::Type::Array);
        CHECK(ctx.get("x").getArray().elements.size() == 3);
        CHECK(ctx.get("x").getArray().elements[0].getInt() == 1);
        CHECK(ctx.get("x").getArray().elements[2].getInt() == 3);
    }

    SECTION("array access") {
        Context ctx;
        eval("x = [10, 20, 30] гойда y = x[1] гойда", ctx);
        CHECK(ctx.get("y").getInt() == 20);
    }

    SECTION("array assignment") {
        Context ctx;
        eval("x = [1, 2, 3] гойда x[1] = 99 гойда", ctx);
        CHECK(ctx.get("x").getArray().elements[1].getInt() == 99);
    }

    SECTION("array create") {
        Context ctx;
        eval("x = созвать_дружину(3, 7) гойда", ctx);
        REQUIRE(ctx.get("x").getType() == Value::Type::Array);
        CHECK(ctx.get("x").getArray().elements.size() == 3);
        CHECK(ctx.get("x").getArray().elements[0].getInt() == 7);
        CHECK(ctx.get("x").getArray().elements[2].getInt() == 7);
    }

    SECTION("array index error") {
        Context ctx;
        CHECK_THROWS_AS(eval("x = [1] гойда y = x[5] гойда", ctx), ValueError);
    }
}

TEST_CASE("Evaluator builtins", "[evaluator]") {
    SECTION("молвить") {
        Context ctx;
        Capture cap;
        eval("молвить(\"hi\") гойда", ctx);
        CHECK(cap.str() == "hi");
    }

    SECTION("тип_значения") {
        Context ctx;
        eval("x = 42 гойда y = тип_значения(x) гойда", ctx);
        CHECK(ctx.get("y").getString() == "цело");
    }

    SECTION("строчить_значение") {
        Context ctx;
        eval("x = 42 гойда y = строчить_значение(x) гойда", ctx);
        CHECK(ctx.get("y").getString() == "42");
    }

    SECTION("имя_аргумента") {
        Context ctx;
        eval("сотвори test(x) изречет строченька ухожу я в пляс возверни имя_аргумента() гойда закончили пляски y = test(42) гойда", ctx);
        CHECK(ctx.get("y").getString() == "x");
    }
}

TEST_CASE("Evaluator complex expressions", "[evaluator]") {
    SECTION("nested arithmetic") {
        Context ctx;
        eval("x = (1 + 2) * 3 гойда", ctx);
        CHECK(ctx.get("x").getInt() == 9);
    }

    SECTION("chained operations") {
        Context ctx;
        eval("x = 1 + 2 + 3 + 4 гойда", ctx);
        CHECK(ctx.get("x").getInt() == 10);
    }

    SECTION("assignment from expression") {
        Context ctx;
        eval("x = 10 гойда y = x * 2 гойда", ctx);
        CHECK(ctx.get("y").getInt() == 20);
    }
}

TEST_CASE("Evaluator return value propagation", "[evaluator]") {
    SECTION("evaluateProgram returns last value") {
        Context ctx;
        auto ast = parse("42 гойда");
        Evaluator ev(&ctx);
        Value result = ev.evaluateProgram(ast);
        CHECK(result.getInt() == 42);
    }

    SECTION("expression statement") {
        Context ctx;
        auto ast = parse("x = 5 гойда x + 3 гойда");
        Evaluator ev(&ctx);
        Value result = ev.evaluateProgram(ast);
        CHECK(result.getInt() == 8);
    }
}
