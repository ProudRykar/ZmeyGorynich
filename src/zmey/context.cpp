#include "context.h"

Context::Context(Context* parent)
    : m_parent(parent) {}

Value Context::get(const std::string& key) const {
    auto it = m_variables.find(key);
    if (it != m_variables.end()) return it->second;
    if (m_parent) return m_parent->get(key);
    return Value();
}

bool Context::hasVariable(const std::string& key) const {
    if (m_variables.find(key) != m_variables.end()) return true;
    if (m_parent) return m_parent->hasVariable(key);
    return false;
}

void Context::set(const std::string& key, const Value& value, const std::string& type_hint) {
    m_variables[key] = value;
    if (!type_hint.empty()) {
        m_type_hints[key] = type_hint;
    }
}

std::string Context::getTypeHint(const std::string& key) const {
    auto it = m_type_hints.find(key);
    if (it != m_type_hints.end()) return it->second;
    if (m_parent) return m_parent->getTypeHint(key);
    return "";
}

void Context::setTypeHint(const std::string& key, const std::string& hint) {
    m_type_hints[key] = hint;
}

bool Context::hasTypeHint(const std::string& key) const {
    if (m_type_hints.find(key) != m_type_hints.end()) return true;
    if (m_parent) return m_parent->hasTypeHint(key);
    return false;
}

void Context::setFunction(const std::string& name, FunctionDef func) {
    m_functions[name] = std::move(func);
}

const FunctionDef* Context::getFunction(const std::string& name) const {
    auto it = m_functions.find(name);
    if (it != m_functions.end()) return &it->second;
    const auto& b = builtins();
    auto bit = b.find(name);
    if (bit != b.end()) return &bit->second;
    if (m_parent) return m_parent->getFunction(name);
    return nullptr;
}

void Context::pushCall(const std::string& name,
                        const std::vector<const ASTNode*>& args_nodes,
                        const std::vector<Value>& args_values) {
    m_call_stack.push_back({name, args_nodes, args_values});
}

void Context::popCall() {
    if (!m_call_stack.empty()) m_call_stack.pop_back();
}

const CallFrame& Context::currentCallFrame() const {
    return m_call_stack.back();
}

std::string Context::getCallArgName(int index) const {
    if (m_call_stack.empty()) return "неизвестно";
    const auto& frame = m_call_stack.back();

    // Try to look up the parameter name from the function definition
    if (!frame.func_name.empty()) {
        auto* func = getFunction(frame.func_name);
        if (func && index < static_cast<int>(func->args.size())) {
            return func->args[index];
        }
    }

    // Fall back to caller's argument node
    if (index < static_cast<int>(frame.args_nodes.size())) {
        const auto* node = frame.args_nodes[index];
        if (node->getType() == NodeType::Identifier) {
            return static_cast<const IdentifierNode*>(node)->name;
        }
        if (node->getType() == NodeType::FunctionCall) {
            return static_cast<const CallNode*>(node)->name + "(...)";
        }
        if (node->getType() == NodeType::Bool) {
            return static_cast<const BoolNode*>(node)->value ? "истина" : "ложь";
        }
        return frame.args_values[index].toString();
    }

    return "неизвестно";
}

const std::unordered_map<std::string, FunctionDef>& Context::builtins() {
    static std::unordered_map<std::string, FunctionDef> b;
    if (b.empty()) {
        // Builtins are registered in builtins.h/.cpp
    }
    return b;
}
