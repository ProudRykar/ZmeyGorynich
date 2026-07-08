#pragma once

#include "ast.h"
#include "value.h"
#include <string>
#include <unordered_map>
#include <vector>

struct FunctionDef {
    std::string name;
    std::vector<std::string> args;
    std::vector<std::string> args_type_hints;
    BlockNode* body = nullptr;
    std::string return_type;
    bool is_builtin = false;
};

struct CallFrame {
    std::string func_name;
    std::vector<const ASTNode*> args_nodes;
    std::vector<Value> args_values;
};

class Context {
public:
    Context(Context* parent = nullptr);

    // Variables
    Value get(const std::string& key) const;
    bool hasVariable(const std::string& key) const;
    void set(const std::string& key, const Value& value, const std::string& type_hint = "");

    // Type hints
    std::string getTypeHint(const std::string& key) const;
    void setTypeHint(const std::string& key, const std::string& hint);
    bool hasTypeHint(const std::string& key) const;

    // Functions
    void setFunction(const std::string& name, FunctionDef func);
    const FunctionDef* getFunction(const std::string& name) const;

    // Call stack
    void pushCall(const std::string& name,
                  const std::vector<const ASTNode*>& args_nodes,
                  const std::vector<Value>& args_values);
    void popCall();
    const CallFrame& currentCallFrame() const;
    bool hasCallStack() const { return !m_call_stack.empty(); }
    std::string getCallArgName(int index = 0) const;

    // Variables access (for importing)
    const std::unordered_map<std::string, Value>& getVariables() const { return m_variables; }

    // Builtins
    static const std::unordered_map<std::string, FunctionDef>& builtins();

private:
    std::unordered_map<std::string, Value> m_variables;
    std::unordered_map<std::string, std::string> m_type_hints;
    std::unordered_map<std::string, FunctionDef> m_functions;
    Context* m_parent = nullptr;
    std::vector<CallFrame> m_call_stack;
};
