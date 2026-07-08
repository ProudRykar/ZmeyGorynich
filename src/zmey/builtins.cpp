#include "builtins.h"
#include "color.h"
#include <iostream>
#include <sstream>

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

static Value builtin_cоздать_дружину(const std::vector<Value>& args, Context* ctx) {
    if (args.size() < 2) throw std::runtime_error("создать_дружину: ожидается 2 аргумента");
    int64_t size = args[0].isNumeric() ? static_cast<int64_t>(args[0].getFloat()) : 0;
    ArrayValue arr;
    arr.elements.resize(size, args[1]);
    return Value(arr);
}

static Value builtin_имя_аргумента(const std::vector<Value>& args, Context* ctx) {
    if (!ctx || !ctx->hasCallStack()) return Value(std::string("неизвестно"));
    return Value(ctx->getCallArgName());
}

static Value builtin_тип_значения(const std::vector<Value>& args, Context* ctx) {
    if (args.empty()) return Value(std::string("пустота"));
    const Value& v = args[0];

    if (ctx && ctx->hasCallStack()) {
        std::string argName = ctx->getCallArgName();
        if (ctx->hasTypeHint(argName)) {
            return Value(mapTypeHintToDisplay(ctx->getTypeHint(argName)));
        }
    }

    return Value(v.typeName());
}

static Value builtin_строчить_значение(const std::vector<Value>& args, Context* ctx) {
    if (args.empty()) return Value(std::string(""));
    return Value(args[0].toString());
}

static Value builtin_молвить(const std::vector<Value>& args, Context* ctx) {
    for (const auto& a : args) {
        std::cout << a.toString();
    }
    return Value();
}

static Value builtin_глас(const std::vector<Value>& args, Context* ctx) {
    if (args.empty() || !ctx) return Value();
    const Value& value = args[0];

    std::string name = ctx->getCallArgName();

    // Determine type name
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

            // Build args display
            std::ostringstream args_str;
            std::string prev_type;
            bool all_same = true;
            for (size_t i = 0; i < frame.args_values.size(); ++i) {
                if (i > 0) args_str << ", ";
                args_str << color::BLUE << frame.args_values[i].toString() << color::RESET;
                std::string arg_type = frame.args_values[i].typeName();
                if (i == 0) prev_type = arg_type;
                else if (arg_type != prev_type) all_same = false;
            }

            std::string call_name = callNode->name + "(";
            for (size_t i = 0; i < frame.args_values.size(); ++i) {
                if (i > 0) call_name += ", ";
                call_name += frame.args_values[i].toString();
            }
            call_name += ")";

            std::string args_display;
            bool has_args = !frame.args_values.empty();
            if (has_args) {
                if (all_same) {
                    args_display = std::string(color::BLUE);
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

    // Simple variable case
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

void registerBuiltins(Context& ctx) {
    FunctionDef молвить_def;
    молвить_def.name = "молвить";
    молвить_def.is_builtin = true;
    ctx.setFunction("молвить", std::move(молвить_def));

    FunctionDef глас_def;
    глас_def.name = "глас";
    глас_def.is_builtin = true;
    ctx.setFunction("глас", std::move(глас_def));

    FunctionDef cоздать_def;
    cоздать_def.name = "созвать_дружину";
    cоздать_def.is_builtin = true;
    ctx.setFunction("созвать_дружину", std::move(cоздать_def));

    FunctionDef имя_арг_def;
    имя_арг_def.name = "имя_аргумента";
    имя_арг_def.is_builtin = true;
    ctx.setFunction("имя_аргумента", std::move(имя_арг_def));

    FunctionDef тип_знач_def;
    тип_знач_def.name = "тип_значения";
    тип_знач_def.is_builtin = true;
    ctx.setFunction("тип_значения", std::move(тип_знач_def));

    FunctionDef строчить_def;
    строчить_def.name = "строчить_значение";
    строчить_def.is_builtin = true;
    ctx.setFunction("строчить_значение", std::move(строчить_def));
}
