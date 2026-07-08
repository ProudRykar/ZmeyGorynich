#pragma once

#include <stdexcept>
#include <string>
#include <vector>

struct ErrorContext {
    int line = 0;
    int col = 0;
    std::string filename;
    std::string fullCode;
};

class ZmeyError : public std::runtime_error {
    ErrorContext m_ctx;
public:
    explicit ZmeyError(const std::string& msg, const ErrorContext& ctx = {})
        : std::runtime_error(msg), m_ctx(ctx) {}

    const ErrorContext& context() const { return m_ctx; }
};

class SyntaxError : public ZmeyError {
public:
    explicit SyntaxError(const std::string& msg, const ErrorContext& ctx = {})
        : ZmeyError(msg, ctx) {}
};

class NameError : public ZmeyError {
public:
    explicit NameError(const std::string& msg, const ErrorContext& ctx = {})
        : ZmeyError(msg, ctx) {}
};

class TypeError : public ZmeyError {
public:
    explicit TypeError(const std::string& msg, const ErrorContext& ctx = {})
        : ZmeyError(msg, ctx) {}
};

class ValueError : public ZmeyError {
public:
    explicit ValueError(const std::string& msg, const ErrorContext& ctx = {})
        : ZmeyError(msg, ctx) {}
};

class RuntimeError : public ZmeyError {
public:
    explicit RuntimeError(const std::string& msg, const ErrorContext& ctx = {})
        : ZmeyError(msg, ctx) {}
};

// Format error message with source code context.
// Returns a multi-line string like:
//   Ошибка: message
//      3 |  x = 42 гойда
//        |      ^
std::string format_error(const ZmeyError& e);
