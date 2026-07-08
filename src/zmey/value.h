#pragma once

#include "decimal.h"
#include <cstdint>
#include <ostream>
#include <string>
#include <vector>

struct ArrayValue {
    std::vector<class Value> elements;
};

class Value {
public:
    enum class Type { Null, Int, Float, Decimal, String, Bool, Array };

    Value();
    Value(int64_t v);
    Value(double v);
    Value(const Decimal& v);
    Value(const std::string& v);
    Value(const char* v);
    Value(bool v);
    Value(const ArrayValue& v);

    Type getType() const { return m_type; }
    bool isNull() const { return m_type == Type::Null; }
    bool isNumeric() const;

    int64_t getInt() const;
    double getFloat() const;
    const Decimal& getDecimal() const;
    const std::string& getString() const;
    bool getBool() const;
    const ArrayValue& getArray() const;
    ArrayValue& getArray();

    std::string toString() const;
    std::string typeName() const;
    std::string inspect() const;

    bool asBool() const;

private:
    Type m_type = Type::Null;
    int64_t m_int = 0;
    double m_float = 0.0;
    Decimal m_decimal;
    std::string m_string;
    bool m_bool = false;
    ArrayValue m_array;
};

std::ostream& operator<<(std::ostream& os, const Value& v);
