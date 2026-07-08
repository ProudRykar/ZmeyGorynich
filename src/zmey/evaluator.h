#pragma once

#include "ast.h"
#include "context.h"
#include "value.h"
#include <string>
#include <vector>

class Evaluator {
public:
    Evaluator(Context* ctx, const std::string& current_file = "");

    Value evaluateProgram(const std::vector<std::unique_ptr<ASTNode>>& ast);
    Value evaluate(const ASTNode& node);
    Value evaluateExpression(const ASTNode& node);
    void evaluateImport(const std::vector<std::unique_ptr<ASTNode>>& ast,
                        Context& module_ctx, const std::string& filepath);

private:
    Context* m_context;
    std::string m_current_file;
    int m_decimal_precision = 100;

    Value evaluateBinaryOp(const BinaryOpNode& node);
    Value evaluateCall(const CallNode& node);

    std::string normalizeOperator(const std::string& op) const;
    void checkType(const Value& value, const std::string& type_hint, const ASTNode& node);
    Value convertValue(const Value& value, const std::string& type_hint);

    Value callFunction(const FunctionDef& func,
                       const std::vector<Value>& args,
                       const std::vector<const ASTNode*>& args_nodes,
                       Context& parent_ctx);

    static Value dispatchBuiltin(const FunctionDef& func,
                                  const std::vector<Value>& args,
                                  const std::vector<const ASTNode*>& args_nodes,
                                  Context* ctx);

    void printFormatted(const PrintNode& node);
};
