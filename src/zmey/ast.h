#pragma once

#include <memory>
#include <string>
#include <vector>

enum class NodeType {
    Number, String, Bool, Identifier, BinaryOp, RootOp,
    Block, If, ElifBranch, ElifBlocks, While, FixedLoop,
    Assignment, ArrayAssignment,
    FunctionDef, FunctionCall, Return,
    Print, Input, Import,
    ArrayLiteral, ArrayAccess, ArrayCreate,
    ExpressionStatement, Args, Arg
};

class ASTNode {
public:
    virtual ~ASTNode() = default;
    virtual NodeType getType() const = 0;
    int line = 0;
    int col = 0;
};

class NumberNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Number; }
    std::string value;
};

class StringNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::String; }
    std::string value;
};

class BoolNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Bool; }
    bool value = false;
};

class IdentifierNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Identifier; }
    std::string name;
};

class BinaryOpNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::BinaryOp; }
    std::unique_ptr<ASTNode> left;
    std::unique_ptr<ASTNode> right;
    std::string op;
};

class RootOpNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::RootOp; }
    std::unique_ptr<ASTNode> expr;
};

class BlockNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Block; }
    std::vector<std::unique_ptr<ASTNode>> statements;
};

class ElifBranchNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::ElifBranch; }
    std::unique_ptr<ASTNode> condition;
    std::unique_ptr<BlockNode> body;
};

class ElifBlocksNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::ElifBlocks; }
    std::vector<std::unique_ptr<ElifBranchNode>> branches;
};

class IfNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::If; }
    std::unique_ptr<ASTNode> condition;
    std::unique_ptr<BlockNode> then_body;
    std::unique_ptr<ElifBlocksNode> elif_blocks;
    std::unique_ptr<BlockNode> else_body;
};

class WhileNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::While; }
    std::unique_ptr<ASTNode> condition;
    std::unique_ptr<BlockNode> body;
};

class FixedLoopNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::FixedLoop; }
    int iterations = 0;
    std::unique_ptr<BlockNode> body;
};

class AssignmentNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Assignment; }
    std::string variable;
    std::unique_ptr<ASTNode> expr;
    std::string type_hint;
};

class ArrayAssignmentNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::ArrayAssignment; }
    std::string variable;
    std::unique_ptr<ASTNode> index;
    std::unique_ptr<ASTNode> expr;
};

class ArgNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Arg; }
    std::string name;
    std::string type_hint;
};

class ArgsNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Args; }
    std::vector<std::unique_ptr<ArgNode>> args;
};

class FunctionDefNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::FunctionDef; }
    std::string name;
    std::unique_ptr<ArgsNode> args;
    std::unique_ptr<BlockNode> body;
    std::string return_type;
};

class ReturnNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Return; }
    std::unique_ptr<ASTNode> expr;
};

class CallNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::FunctionCall; }
    std::string name;
    std::vector<std::unique_ptr<ASTNode>> args;
};

class PrintNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Print; }
    std::vector<std::unique_ptr<ASTNode>> args;
    bool silent = false;
};

class InputNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Input; }
    std::unique_ptr<ASTNode> prompt;
    std::string variable;
};

class ImportNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Import; }
    std::string filename;
    std::string alias;
};

class ArrayLiteralNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::ArrayLiteral; }
    std::vector<std::unique_ptr<ASTNode>> elements;
};

class ArrayAccessNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::ArrayAccess; }
    std::unique_ptr<ASTNode> array;
    std::unique_ptr<ASTNode> index;
};

class ArrayCreateNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::ArrayCreate; }
    std::unique_ptr<ASTNode> size;
    std::unique_ptr<ASTNode> value;
};

class ExpressionStatementNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::ExpressionStatement; }
    std::unique_ptr<ASTNode> expr;
};
