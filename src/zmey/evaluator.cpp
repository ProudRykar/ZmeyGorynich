#include "evaluator.h"
#include "color.h"
#include "error.h"
#include "lexer.h"
#include "parser.h"
#include <cmath>
#include <fstream>
#include <iostream>
#include <sstream>

Evaluator::Evaluator(Context* ctx, const std::string& current_file)
    : m_context(ctx), m_current_file(current_file) {}

// --- helpers ---
static ErrorContext errorCtx(const ASTNode& node, const std::string& code = "") {
    ErrorContext ctx;
    ctx.line = node.line;
    ctx.col = node.col;
    ctx.fullCode = code;
    return ctx;
}

static std::string mapTypeHintToDisplay(const std::string& type_hint) {
    if (type_hint == "двосуть") return "двосуть";
    if (type_hint == "строченька") return "строченька";
    if (type_hint == "число:int") return "цело";
    if (type_hint == "число:float") return "плывун";
    if (type_hint == "decimal:30") return "плывун малый точный";
    if (type_hint == "decimal:50") return "плывун великий";
    if (type_hint == "decimal:100") return "плывун звёздный";
    if (type_hint.substr(0, 5) == "list:") {
        return "список " + mapTypeHintToDisplay(type_hint.substr(5));
    }
    return type_hint;
}

static Value builtin_глас_func(const std::vector<Value>& args, Context* ctx) {
    if (args.empty() || !ctx) return Value();
    const Value& value = args[0];

    std::string name = ctx->getCallArgName(0);
    std::string type_name;

    if (ctx->hasCallStack()) {
        const auto& frame = ctx->currentCallFrame();
        bool is_function_call = !frame.args_nodes.empty() &&
            frame.args_nodes[0]->getType() == NodeType::FunctionCall;

        if (is_function_call) {
            const auto* callNode = static_cast<const CallNode*>(frame.args_nodes[0]);
            const auto* funcDef = ctx->getFunction(callNode->name);
            if (funcDef && !funcDef->return_type.empty()) {
                type_name = mapTypeHintToDisplay(funcDef->return_type);
            } else {
                type_name = value.typeName();
            }

            std::string call_name = callNode->name + "(";
            for (size_t i = 0; i < frame.args_values.size(); ++i) {
                if (i > 0) call_name += ", ";
                call_name += frame.args_values[i].toString();
            }
            call_name += ")";

            std::string args_display;
            if (!frame.args_values.empty()) {
                std::string prev_type;
                bool all_same = true;
                for (size_t i = 0; i < frame.args_values.size(); ++i) {
                    std::string at = frame.args_values[i].typeName();
                    if (i == 0) prev_type = at;
                    else if (at != prev_type) all_same = false;
                }

                if (all_same) {
                    args_display += std::string(color::BLUE);
                    for (size_t i = 0; i < frame.args_values.size(); ++i) {
                        if (i > 0) args_display += ", ";
                        args_display += frame.args_values[i].toString();
                    }
                    args_display += std::string(color::RESET) + " быти " + color::YELLOW + prev_type + color::RESET;
                } else {
                    for (size_t i = 0; i < frame.args_values.size(); ++i) {
                        if (i > 0) args_display += ", ";
                        args_display += std::string(color::BLUE) + frame.args_values[i].toString() + color::RESET +
                                        " быти " + color::YELLOW + frame.args_values[i].typeName() + color::RESET;
                    }
                }
            }

            std::cout << color::CYAN << "ᚨᛇᛟ: "
                      << color::MAGENTA << call_name << color::RESET
                      << " -> "
                      << color::GREEN << args_display << color::RESET
                      << " -> " << color::BLUE << value.toString() << color::RESET
                      << " быти " << color::YELLOW << type_name << color::RESET
                      << "\n";
            return value;
        }
    }

    if (ctx->hasTypeHint(name)) {
        type_name = mapTypeHintToDisplay(ctx->getTypeHint(name));
    } else {
        type_name = value.typeName();
    }

    std::cout << color::CYAN << "ᚨᛇᛟ: "
              << color::GREEN << name << color::RESET
              << " -> "
              << color::BLUE << value.toString() << color::RESET
              << " быти " << color::YELLOW << type_name << color::RESET
              << "\n";
    return value;
}

// --- normalizeOperator ---
std::string Evaluator::normalizeOperator(const std::string& op) const {
    std::string o = op;
    for (auto& c : o) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    if (!o.empty() && o.back() == ':') o.pop_back();
    for (size_t i = 0; i + 1 < o.size(); ++i) {
        if (static_cast<unsigned char>(o[i]) == 0xD1 &&
            static_cast<unsigned char>(o[i + 1]) == 0x91) {
            o[i] = 0xD0;
            o[i + 1] = 0xB5;
        }
    }

    static const std::unordered_map<std::string, std::string> mapping = {
        {"прибави", "+"}, {"прибавить", "+"}, {"плюс", "+"},
        {"отними", "-"}, {"вычти", "-"}, {"минус", "-"},
        {"умножи на", "*"}, {"умножить на", "*"}, {"умножи", "*"},
        {"раздели на", "/"}, {"разделить на", "/"}, {"дели на", "/"},
        {"остаток от", "%"}, {"мод", "%"},
        {"возвысить в", "**"}, {"возвысить", "**"}, {"возвести в", "**"}, {"в степенне", "**"},
        {"превосходит", ">"}, {"превышает", ">"}, {"больше", ">"},
        {"уступает", "<"}, {"меньше", "<"}, {"меньше чем", "<"},
        {"ровно", "=="}, {"равно", "=="}, {"есть", "=="}, {"равно ли", "=="},
        {"не равно", "!="}, {"неравно", "!="}, {"не равно ли", "!="}, {"не есть", "!="},
        {"ровно либо превосходит", ">="}, {"ровно или превосходит", ">="}, {"больше или равно", ">="},
        {"ровно либо уступает", "<="}, {"ровно или уступает", "<="}, {"меньше или равно", "<="},
        {">", ">"}, {"<", "<"}, {">=", ">="}, {"<=", "<="},
        {"==", "=="}, {"!=", "!="},
    };

    auto it = mapping.find(o);
    if (it != mapping.end()) return it->second;
    return o;
}

// --- checkType ---
void Evaluator::checkType(const Value& value, const std::string& type_hint, const ASTNode& node) {
    if (type_hint.empty()) return;
    auto ctx = errorCtx(node);

    if (type_hint == "строченька") {
        if (value.getType() != Value::Type::String)
            throw TypeError("Значение должно быть строченькой, а не " + value.typeName(), ctx);
    } else if (type_hint == "двосуть") {
        if (value.getType() != Value::Type::Bool)
            throw TypeError("Значение должно быть двосутью, а не " + value.typeName(), ctx);
    } else if (type_hint == "число:int") {
        if (!value.isNumeric())
            throw TypeError("Значение должно быть целым числом, а не " + value.typeName(), ctx);
        if (value.getType() == Value::Type::Float)
            throw TypeError("Значение должно быть целым числом (цело), а не плывун", ctx);
    } else if (type_hint == "число:float") {
        if (!value.isNumeric())
            throw TypeError("Значение должно быть числом, а не " + value.typeName(), ctx);
    } else if (type_hint.substr(0, 8) == "decimal:") {
        if (value.getType() != Value::Type::Decimal)
            throw TypeError("Значение должно быть числом высокой точности, а не " + value.typeName(), ctx);
    } else if (type_hint.substr(0, 5) == "list:" || type_hint.substr(0, 7) == "список ") {
        if (value.getType() != Value::Type::Array)
            throw TypeError("Значение должно быть списком, а не " + value.typeName(), ctx);
    }
}

// --- convertValue ---
Value Evaluator::convertValue(const Value& value, const std::string& type_hint) {
    if (type_hint.empty()) return value;

    if (type_hint == "число:int") {
        if (value.getType() == Value::Type::Int) return value;
        if (value.getType() == Value::Type::Float) return Value(static_cast<int64_t>(value.getFloat()));
        if (value.getType() == Value::Type::Decimal) return Value(value.getDecimal().toInt64());
        if (value.getType() == Value::Type::String) {
            try { return Value(static_cast<int64_t>(std::stoll(value.getString()))); }
            catch (...) { throw TypeError("Неверное значение для целого числа: " + value.getString(), {}); }
        }
        throw TypeError("Нельзя преобразовать " + value.typeName() + " в цело", {});
    }
    if (type_hint == "число:float") {
        if (value.getType() == Value::Type::Float) return value;
        if (value.getType() == Value::Type::Int) return Value(static_cast<double>(value.getInt()));
        if (value.getType() == Value::Type::Decimal) return Value(value.getDecimal().toDouble());
        if (value.getType() == Value::Type::String) {
            try { return Value(std::stod(value.getString())); }
            catch (...) { throw TypeError("Неверное значение для числа: " + value.getString(), {}); }
        }
        throw TypeError("Нельзя преобразовать " + value.typeName() + " в плывун", {});
    }
    if (type_hint.substr(0, 8) == "decimal:") {
        if (value.getType() == Value::Type::Decimal) return value;
        if (value.getType() == Value::Type::Int) return Value(Decimal(std::to_string(value.getInt())));
        if (value.getType() == Value::Type::Float) return Value(Decimal(std::to_string(value.getFloat())));
        if (value.getType() == Value::Type::String) {
            try { return Value(Decimal(value.getString())); }
            catch (...) { throw TypeError("Неверное значение для числа высокой точности: " + value.getString(), {}); }
        }
        throw TypeError("Нельзя преобразовать " + value.typeName() + " в плывун высокой точности", {});
    }
    if (type_hint == "строченька") {
        if (value.getType() == Value::Type::String) return value;
        return Value(value.toString());
    }
    if (type_hint == "двосуть") {
        if (value.getType() == Value::Type::Bool) return value;
        return Value(value.asBool());
    }

    return value;
}

// --- evaluateExpression ---
Value Evaluator::evaluateExpression(const ASTNode& node) {
    switch (node.getType()) {
        case NodeType::Number: {
            const auto& numNode = static_cast<const NumberNode&>(node);
            std::string val = numNode.value;
            if (val.find('.') != std::string::npos || val.find('e') != std::string::npos || val.find('E') != std::string::npos) {
                try { return Value(Decimal(val)); }
                catch (...) { return Value(std::stod(val)); }
            }
            try { return Value(static_cast<int64_t>(std::stoll(val))); }
            catch (...) { return Value(Decimal(val)); }
        }
        case NodeType::String: {
            const auto& strNode = static_cast<const StringNode&>(node);
            std::string val = strNode.value;
            if (val.size() >= 2 && val.front() == '"' && val.back() == '"')
                val = val.substr(1, val.size() - 2);
            return Value(val);
        }
        case NodeType::Bool: {
            const auto& boolNode = static_cast<const BoolNode&>(node);
            return Value(boolNode.value);
        }
        case NodeType::Identifier: {
            const auto& idNode = static_cast<const IdentifierNode&>(node);
            if (m_context->hasVariable(idNode.name))
                return m_context->get(idNode.name);
            auto dotPos = idNode.name.find('.');
            if (dotPos != std::string::npos) {
                std::string varName = idNode.name.substr(dotPos + 1);
                if (m_context->hasVariable(varName))
                    return m_context->get(varName);
                throw NameError("Модуль '" + idNode.name.substr(0, dotPos) + "' не найден", errorCtx(node));
            }
            throw NameError("Переменная '" + idNode.name + "' не определена", errorCtx(node));
        }
        case NodeType::BinaryOp: {
            return evaluateBinaryOp(static_cast<const BinaryOpNode&>(node));
        }
        case NodeType::RootOp: {
            const auto& rootNode = static_cast<const RootOpNode&>(node);
            Value val = evaluateExpression(*rootNode.expr);
            if (!val.isNumeric())
                throw ValueError("Корень можно извлечь только из числа", errorCtx(node));
            if (val.getType() == Value::Type::Decimal)
                return Value(val.getDecimal().sqrt());
            double d = (val.getType() == Value::Type::Int) ? static_cast<double>(val.getInt()) : val.getFloat();
            double result = std::sqrt(d);
            if (result == std::floor(result) && std::isfinite(result))
                return Value(static_cast<int64_t>(result));
            return Value(result);
        }
        case NodeType::FunctionCall: {
            return evaluateCall(static_cast<const CallNode&>(node));
        }
        case NodeType::ArrayLiteral: {
            const auto& arrNode = static_cast<const ArrayLiteralNode&>(node);
            ArrayValue arr;
            for (const auto& elem : arrNode.elements)
                arr.elements.push_back(evaluateExpression(*elem));
            return Value(arr);
        }
        case NodeType::ArrayAccess: {
            const auto& accessNode = static_cast<const ArrayAccessNode&>(node);
            Value arrVal = evaluateExpression(*accessNode.array);
            Value idxVal = evaluateExpression(*accessNode.index);
            if (arrVal.getType() != Value::Type::Array)
                throw ValueError("Индексация возможна только для массивов", errorCtx(node));
            int64_t index = idxVal.isNumeric() ? static_cast<int64_t>(idxVal.getFloat()) : 0;
            const auto& arr = arrVal.getArray();
            if (index < 0 || index >= static_cast<int64_t>(arr.elements.size()))
                throw ValueError("Недопустимый индекс " + std::to_string(index), errorCtx(node));
            return arr.elements[index];
        }
        case NodeType::ArrayCreate: {
            const auto& createNode = static_cast<const ArrayCreateNode&>(node);
            Value sizeVal = evaluateExpression(*createNode.size);
            Value valVal = evaluateExpression(*createNode.value);
            int64_t size = sizeVal.isNumeric() ? static_cast<int64_t>(sizeVal.getFloat()) : 0;
            if (size < 0) throw ValueError("Размер массива должен быть неотрицательным", errorCtx(node));
            ArrayValue arr;
            arr.elements.resize(size, valVal);
            return Value(arr);
        }
        case NodeType::ExpressionStatement: {
            const auto& exprStmt = static_cast<const ExpressionStatementNode&>(node);
            return evaluateExpression(*exprStmt.expr);
        }
        default:
            return Value();
    }
}

// --- evaluateBinaryOp ---
Value Evaluator::evaluateBinaryOp(const BinaryOpNode& node) {
    std::string op = normalizeOperator(node.op);
    Value left = evaluateExpression(*node.left);
    Value right = evaluateExpression(*node.right);

    if (op == "<") {
        if (left.isNumeric() && right.isNumeric())
            return Value(left.getFloat() < right.getFloat());
        return Value(left.asBool() < right.asBool());
    }
    if (op == ">") {
        if (left.isNumeric() && right.isNumeric())
            return Value(left.getFloat() > right.getFloat());
        return Value(left.asBool() > right.asBool());
    }
    if (op == "<=") {
        if (left.isNumeric() && right.isNumeric())
            return Value(left.getFloat() <= right.getFloat());
        return Value(left.asBool() <= right.asBool());
    }
    if (op == ">=") {
        if (left.isNumeric() && right.isNumeric())
            return Value(left.getFloat() >= right.getFloat());
        return Value(left.asBool() >= right.asBool());
    }
    if (op == "==") {
        if (left.isNumeric() && right.isNumeric()) {
            if (left.getType() == Value::Type::Decimal || right.getType() == Value::Type::Decimal) {
                Decimal a = (left.getType() == Value::Type::Decimal) ? left.getDecimal() : Decimal(std::to_string(left.getFloat()));
                Decimal b = (right.getType() == Value::Type::Decimal) ? right.getDecimal() : Decimal(std::to_string(right.getFloat()));
                return Value(a == b);
            }
            if (left.getType() == Value::Type::Float || right.getType() == Value::Type::Float)
                return Value(left.getFloat() == right.getFloat());
            return Value(left.getInt() == right.getInt());
        }
        if (left.getType() != right.getType()) return Value(false);
        if (left.getType() == Value::Type::String) return Value(left.getString() == right.getString());
        if (left.getType() == Value::Type::Bool) return Value(left.getBool() == right.getBool());
        return Value(false);
    }
    if (op == "!=") {
        if (left.isNumeric() && right.isNumeric()) {
            if (left.getType() == Value::Type::Decimal || right.getType() == Value::Type::Decimal) {
                Decimal a = (left.getType() == Value::Type::Decimal) ? left.getDecimal() : Decimal(std::to_string(left.getFloat()));
                Decimal b = (right.getType() == Value::Type::Decimal) ? right.getDecimal() : Decimal(std::to_string(right.getFloat()));
                return Value(a != b);
            }
            if (left.getType() == Value::Type::Float || right.getType() == Value::Type::Float)
                return Value(left.getFloat() != right.getFloat());
            return Value(left.getInt() != right.getInt());
        }
        if (left.getType() != right.getType()) return Value(true);
        if (left.getType() == Value::Type::String) return Value(left.getString() != right.getString());
        if (left.getType() == Value::Type::Bool) return Value(left.getBool() != right.getBool());
        return Value(true);
    }

    // String concat
    if (op == "+" && (left.getType() == Value::Type::String || right.getType() == Value::Type::String))
        return Value(left.toString() + right.toString());

    // Array concat
    if (op == "+" && left.getType() == Value::Type::Array && right.getType() == Value::Type::Array) {
        ArrayValue result = left.getArray();
        for (const auto& elem : right.getArray().elements)
            result.elements.push_back(elem);
        return Value(result);
    }

    if (!left.isNumeric() || !right.isNumeric())
        throw ValueError("Операция '" + op + "' требует числа", errorCtx(node));

    bool useDecimal = (left.getType() == Value::Type::Decimal || right.getType() == Value::Type::Decimal);

    if (useDecimal) {
        Decimal a = (left.getType() == Value::Type::Decimal) ? left.getDecimal() : Decimal(std::to_string(left.getFloat()));
        Decimal b = (right.getType() == Value::Type::Decimal) ? right.getDecimal() : Decimal(std::to_string(right.getFloat()));
        if (op == "+") return Value(a + b);
        if (op == "-") return Value(a - b);
        if (op == "*") return Value(a * b);
        if (op == "/") { if (b.isZero()) throw ValueError("Деление на ноль", errorCtx(node)); return Value(a / b); }
        if (op == "%") { if (b.isZero()) throw ValueError("Деление на ноль", errorCtx(node)); return Value(Decimal(std::to_string(static_cast<int64_t>(a.toDouble()) % static_cast<int64_t>(b.toDouble())))); }
        if (op == "**") return Value(Decimal(std::to_string(std::pow(a.toDouble(), b.toDouble()))));
    } else {
        if (left.getType() == Value::Type::Int && right.getType() == Value::Type::Int) {
            if (op == "+") return Value(left.getInt() + right.getInt());
            if (op == "-") return Value(left.getInt() - right.getInt());
            if (op == "*") return Value(left.getInt() * right.getInt());
            if (op == "/") { if (right.getInt() == 0) throw ValueError("Деление на ноль", errorCtx(node)); return Value(static_cast<double>(left.getInt()) / static_cast<double>(right.getInt())); }
            if (op == "%") { if (right.getInt() == 0) throw ValueError("Деление на ноль", errorCtx(node)); return Value(left.getInt() % right.getInt()); }
            if (op == "**") { double r = std::pow(left.getInt(), right.getInt()); return Value(static_cast<int64_t>(r)); }
        }
        double a = left.getFloat(), b = right.getFloat();
        if (op == "+") return Value(a + b);
        if (op == "-") return Value(a - b);
        if (op == "*") return Value(a * b);
        if (op == "/") { if (b == 0.0) throw ValueError("Деление на ноль", errorCtx(node)); return Value(a / b); }
        if (op == "%") return Value(std::fmod(a, b));
        if (op == "**") { double r = std::pow(a, b); return Value(r); }
    }

    throw ValueError("Неизвестная операция: " + op, errorCtx(node));
}

// --- evaluateCall ---
Value Evaluator::evaluateCall(const CallNode& node) {
    const FunctionDef* func = m_context->getFunction(node.name);
    if (!func)
        throw NameError("Функция '" + node.name + "' не определена", errorCtx(node));

    std::vector<Value> args;
    for (const auto& arg : node.args)
        args.push_back(evaluateExpression(*arg));

    std::vector<const ASTNode*> argNodes;
    for (const auto& arg : node.args) argNodes.push_back(arg.get());

    if (func->is_builtin) {
        if (node.name == "имя_аргумента") {
            return dispatchBuiltin(*func, args, argNodes, m_context);
        }
        m_context->pushCall(node.name, argNodes, args);
        Value result = dispatchBuiltin(*func, args, argNodes, m_context);
        m_context->popCall();
        return result;
    }

    return callFunction(*func, args, argNodes, *m_context);
}

// --- dispatchBuiltin ---
Value Evaluator::dispatchBuiltin(const FunctionDef& func,
                                  const std::vector<Value>& args,
                                  const std::vector<const ASTNode*>& args_nodes,
                                  Context* ctx) {
    if (func.name == "молвить") {
        for (const auto& a : args) std::cout << a.toString();
        return Value();
    }
    if (func.name == "глас") return builtin_глас_func(args, ctx);
    if (func.name == "созвать_дружину") {
        if (args.size() < 2) throw std::runtime_error("созвать_дружину: 2 аргумента");
        int64_t size = args[0].isNumeric() ? static_cast<int64_t>(args[0].getFloat()) : 0;
        ArrayValue arr;
        arr.elements.resize(size, args[1]);
        return Value(arr);
    }
    if (func.name == "имя_аргумента") {
        if (!ctx || !ctx->hasCallStack()) return Value(std::string("неизвестно"));
        return Value(ctx->getCallArgName());
    }
    if (func.name == "тип_значения") {
        if (args.empty()) return Value(std::string("пустота"));
        if (ctx && ctx->hasCallStack()) {
            std::string argName = ctx->getCallArgName(0);
            if (ctx->hasTypeHint(argName))
                return Value(mapTypeHintToDisplay(ctx->getTypeHint(argName)));
        }
        return Value(args[0].typeName());
    }
    if (func.name == "строчить_значение") {
        if (args.empty()) return Value(std::string(""));
        return Value(args[0].toString());
    }
    return Value();
}

// --- callFunction ---
Value Evaluator::callFunction(const FunctionDef& func,
                               const std::vector<Value>& args,
                               const std::vector<const ASTNode*>& args_nodes,
                               Context& parent_ctx) {
    if (args.size() != func.args.size()) {
        throw ValueError("Функция '" + func.name + "' ожидает " + std::to_string(func.args.size()) +
                         " аргументов, получено " + std::to_string(args.size()), {});
    }

    Context local_ctx(&parent_ctx);
    local_ctx.pushCall(func.name, args_nodes, args);

    for (size_t i = 0; i < func.args.size(); ++i) {
        Value argVal = args[i];
        std::string typeHint;
        if (i < func.args_type_hints.size()) typeHint = func.args_type_hints[i];
        if (!typeHint.empty()) argVal = convertValue(argVal, typeHint);
        local_ctx.set(func.args[i], argVal, typeHint);
    }

    Context* saved_ctx = m_context;
    m_context = &local_ctx;

    Value result;
    if (func.body) {
        for (const auto& stmt : func.body->statements) {
            result = evaluate(*stmt);
        }
    }

    m_context = saved_ctx;
    local_ctx.popCall();

    if (!func.return_type.empty()) {
        result = convertValue(result, func.return_type);
        checkType(result, func.return_type, *func.body);
    }

    return result;
}

// --- evaluate ---
Value Evaluator::evaluate(const ASTNode& node) {
    switch (node.getType()) {
        case NodeType::Print: {
            const auto& printNode = static_cast<const PrintNode&>(node);
            for (const auto& arg : printNode.args) {
                std::cout << evaluateExpression(*arg).toString();
            }
            if (printNode.silent) std::cout << "\n";
            return Value();
        }
        case NodeType::Input: {
            const auto& inputNode = static_cast<const InputNode&>(node);
            std::string prompt;
            if (inputNode.prompt)
                prompt = evaluateExpression(*inputNode.prompt).toString();
            std::string userInput;
            std::cout << prompt;
            std::getline(std::cin, userInput);

            Value inputValue;
            try { inputValue = Value(static_cast<int64_t>(std::stoll(userInput))); }
            catch (...) {
                try { inputValue = Value(std::stod(userInput)); }
                catch (...) {
                    if (userInput == "истина") inputValue = Value(true);
                    else if (userInput == "ложь") inputValue = Value(false);
                    else inputValue = Value(userInput);
                }
            }

            std::string typeHint = m_context->getTypeHint(inputNode.variable);
            if (!typeHint.empty()) {
                inputValue = convertValue(inputValue, typeHint);
                checkType(inputValue, typeHint, node);
            }
            m_context->set(inputNode.variable, inputValue);
            return Value();
        }
        case NodeType::Assignment: {
            const auto& assignNode = static_cast<const AssignmentNode&>(node);
            Value exprVal = evaluateExpression(*assignNode.expr);
            if (!assignNode.type_hint.empty()) {
                exprVal = convertValue(exprVal, assignNode.type_hint);
                checkType(exprVal, assignNode.type_hint, node);
            }
            m_context->set(assignNode.variable, exprVal, assignNode.type_hint);
            return Value();
        }
        case NodeType::ArrayAssignment: {
            const auto& arrAssign = static_cast<const ArrayAssignmentNode&>(node);
            Value arrVal = m_context->get(arrAssign.variable);
            if (arrVal.getType() != Value::Type::Array)
                throw ValueError(arrAssign.variable + " не является массивом", errorCtx(node));
            Value indexVal = evaluateExpression(*arrAssign.index);
            Value valVal = evaluateExpression(*arrAssign.expr);
            int64_t index = indexVal.isNumeric() ? static_cast<int64_t>(indexVal.getFloat()) : 0;
            auto& arr = arrVal.getArray();
            if (index < 0 || index >= static_cast<int64_t>(arr.elements.size()))
                throw ValueError("Недопустимый индекс", errorCtx(node));
            arr.elements[index] = valVal;
            m_context->set(arrAssign.variable, arrVal);
            return Value();
        }
        case NodeType::While: {
            const auto& whileNode = static_cast<const WhileNode&>(node);
            while (true) {
                Value cond = evaluateExpression(*whileNode.condition);
                if (!cond.asBool()) break;
                for (const auto& stmt : whileNode.body->statements) {
                    Value result = evaluate(*stmt);
                    if (result.getType() != Value::Type::Null) return result;
                }
            }
            return Value();
        }
        case NodeType::If: {
            const auto& ifNode = static_cast<const IfNode&>(node);
            Value cond = evaluateExpression(*ifNode.condition);
            if (cond.asBool()) {
                for (const auto& stmt : ifNode.then_body->statements) {
                    Value result = evaluate(*stmt);
                    if (result.getType() != Value::Type::Null) return result;
                }
                return Value();
            }
            for (const auto& elifBranch : ifNode.elif_blocks->branches) {
                Value elifCond = evaluateExpression(*elifBranch->condition);
                if (elifCond.asBool()) {
                    for (const auto& stmt : elifBranch->body->statements) {
                        Value result = evaluate(*stmt);
                        if (result.getType() != Value::Type::Null) return result;
                    }
                    return Value();
                }
            }
            if (ifNode.else_body) {
                for (const auto& stmt : ifNode.else_body->statements) {
                    Value result = evaluate(*stmt);
                    if (result.getType() != Value::Type::Null) return result;
                }
            }
            return Value();
        }
        case NodeType::FunctionDef: {
            const auto& funcNode = static_cast<const FunctionDefNode&>(node);
            FunctionDef func;
            func.name = funcNode.name;
            func.return_type = funcNode.return_type;
            func.body = funcNode.body.get();
            for (const auto& arg : funcNode.args->args) {
                func.args.push_back(arg->name);
                func.args_type_hints.push_back(arg->type_hint);
            }
            m_context->setFunction(funcNode.name, std::move(func));
            return Value();
        }
        case NodeType::Return: {
            const auto& retNode = static_cast<const ReturnNode&>(node);
            return evaluateExpression(*retNode.expr);
        }
        case NodeType::FixedLoop: {
            const auto& loopNode = static_cast<const FixedLoopNode&>(node);
            for (int i = 0; i < loopNode.iterations; ++i) {
                for (const auto& stmt : loopNode.body->statements) {
                    Value result = evaluate(*stmt);
                    if (result.getType() != Value::Type::Null) return result;
                }
            }
            return Value();
        }
        case NodeType::Import: {
            const auto& importNode = static_cast<const ImportNode&>(node);
            std::string filename = importNode.filename;
            std::string filepath = filename;
            if (!m_current_file.empty()) {
                size_t slashPos = m_current_file.find_last_of("/\\");
                if (slashPos != std::string::npos) {
                    std::string dir = m_current_file.substr(0, slashPos);
                    std::string rp = dir + "/" + filename;
                    std::ifstream tf(rp);
                    if (tf) filepath = rp;
                }
            }
            std::ifstream file(filepath);
            if (!file) throw std::runtime_error("Файл '" + filename + "' не найден");
            std::stringstream buffer;
            buffer << file.rdbuf();
            std::string code = buffer.str();

            Lexer lexer(code);
            auto tokens = lexer.tokenize();
            Parser parser(tokens, code);
            auto ast = parser.parse();

            // Register functions from imported file
            for (const auto& stmt : ast) {
                if (stmt->getType() == NodeType::FunctionDef) {
                    auto* fn = static_cast<FunctionDefNode*>(stmt.get());
                    FunctionDef f;
                    f.name = fn->name;
                    f.return_type = fn->return_type;
                    f.body = fn->body.get();
                    for (const auto& arg : fn->args->args) {
                        f.args.push_back(arg->name);
                        f.args_type_hints.push_back(arg->type_hint);
                    }
                    m_context->setFunction(fn->name, std::move(f));
                }
            }
            // Merge variables under alias
            Context module_ctx(m_context);
            for (const auto& stmt : ast) {
                if (stmt->getType() == NodeType::Assignment) {
                    auto* as = static_cast<AssignmentNode*>(stmt.get());
                    Value val = evaluateExpression(*as->expr);
                    module_ctx.set(as->variable, val, as->type_hint);
                }
            }
            for (const auto& [key, val] : module_ctx.getVariables()) {
                m_context->set(key, val);
                if (!importNode.alias.empty() && importNode.alias != "гойда") {
                    m_context->set(importNode.alias + "." + key, val);
                }
            }

            return Value();
        }
        default:
            return evaluateExpression(node);
    }
}

// --- evaluateImport ---
void Evaluator::evaluateImport(const std::vector<std::unique_ptr<ASTNode>>& ast,
                                Context& module_ctx, const std::string& filepath) {
    for (const auto& node : ast) {
        if (node->getType() == NodeType::Assignment) {
            const auto& assign = static_cast<const AssignmentNode&>(*node);
            Value val = evaluateExpression(*assign.expr);
            if (!assign.type_hint.empty()) {
                val = convertValue(val, assign.type_hint);
                checkType(val, assign.type_hint, *node);
            }
            module_ctx.set(assign.variable, val, assign.type_hint);
        } else if (node->getType() == NodeType::FunctionDef) {
            const auto& funcNode = static_cast<const FunctionDefNode&>(*node);
            FunctionDef func;
            func.name = funcNode.name;
            func.return_type = funcNode.return_type;
            func.body = funcNode.body.get();
            for (const auto& arg : funcNode.args->args) {
                func.args.push_back(arg->name);
                func.args_type_hints.push_back(arg->type_hint);
            }
            module_ctx.setFunction(funcNode.name, std::move(func));
        }
    }
}

// --- evaluateProgram ---
Value Evaluator::evaluateProgram(const std::vector<std::unique_ptr<ASTNode>>& ast) {
    Value result;
    for (const auto& node : ast)
        result = evaluate(*node);
    return result;
}
