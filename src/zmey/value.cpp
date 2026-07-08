#include "value.h"
#include <sstream>

Value::Value() : m_type(Type::Null) {}

Value::Value(int64_t v) : m_type(Type::Int), m_int(v) {}

Value::Value(double v) : m_type(Type::Float), m_float(v) {}

Value::Value(const Decimal& v) : m_type(Type::Decimal), m_decimal(v) {}

Value::Value(const std::string& v) : m_type(Type::String), m_string(v) {}

Value::Value(const char* v) : m_type(Type::String), m_string(v) {}

Value::Value(bool v) : m_type(Type::Bool), m_bool(v) {}

Value::Value(const ArrayValue& v) : m_type(Type::Array), m_array(v) {}

bool Value::isNumeric() const {
    return m_type == Type::Int || m_type == Type::Float || m_type == Type::Decimal;
}

int64_t Value::getInt() const {
    switch (m_type) {
        case Type::Int: return m_int;
        case Type::Float: return static_cast<int64_t>(m_float);
        case Type::Decimal: return m_decimal.toInt64();
        default: return 0;
    }
}

double Value::getFloat() const {
    switch (m_type) {
        case Type::Float: return m_float;
        case Type::Int: return static_cast<double>(m_int);
        case Type::Decimal: return m_decimal.toDouble();
        default: return 0.0;
    }
}

const Decimal& Value::getDecimal() const {
    return m_decimal;
}

const std::string& Value::getString() const {
    return m_string;
}

bool Value::getBool() const {
    return m_bool;
}

const ArrayValue& Value::getArray() const {
    return m_array;
}

ArrayValue& Value::getArray() {
    return m_array;
}

bool Value::asBool() const {
    switch (m_type) {
        case Type::Null: return false;
        case Type::Int: return m_int != 0;
        case Type::Float: return m_float != 0.0;
        case Type::Decimal: return !m_decimal.isZero();
        case Type::String: return !m_string.empty();
        case Type::Bool: return m_bool;
        case Type::Array: return !m_array.elements.empty();
    }
    return false;
}

std::string Value::toString() const {
    switch (m_type) {
        case Type::Null: return "пустота";
        case Type::Int: return std::to_string(m_int);
        case Type::Float: {
            std::string s = std::to_string(m_float);
            // Remove trailing zeros
            auto dot = s.find('.');
            if (dot != std::string::npos) {
                s.erase(s.find_last_not_of('0') + 1, std::string::npos);
                if (s.back() == '.') s.pop_back();
            }
            return s;
        }
        case Type::Decimal: return m_decimal.toString();
        case Type::String: return m_string;
        case Type::Bool: return m_bool ? "Истина" : "Ложь";
        case Type::Array: {
            std::string s = "[";
            for (size_t i = 0; i < m_array.elements.size(); ++i) {
                if (i > 0) s += ", ";
                s += m_array.elements[i].toString();
            }
            s += "]";
            return s;
        }
    }
    return "";
}

std::string Value::typeName() const {
    switch (m_type) {
        case Type::Null: return "пустота";
        case Type::Int: return "цело";
        case Type::Float: return "плывун";
        case Type::Decimal: return "плывун звёздный";
        case Type::String: return "строченька";
        case Type::Bool: return "двосуть";
        case Type::Array: return "список";
    }
    return "неизвестно";
}

std::string Value::inspect() const {
    std::ostringstream oss;
    oss << "Value(";
    switch (m_type) {
        case Type::Null: oss << "Null"; break;
        case Type::Int: oss << "Int: " << m_int; break;
        case Type::Float: oss << "Float: " << m_float; break;
        case Type::Decimal: oss << "Decimal: " << m_decimal.toString(); break;
        case Type::String: oss << "String: \"" << m_string << "\""; break;
        case Type::Bool: oss << "Bool: " << (m_bool ? "true" : "false"); break;
        case Type::Array: oss << "Array[" << m_array.elements.size() << "]"; break;
    }
    oss << ")";
    return oss.str();
}

std::ostream& operator<<(std::ostream& os, const Value& v) {
    os << v.toString();
    return os;
}
