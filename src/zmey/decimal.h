#pragma once

#include <cstdint>
#include <ostream>
#include <string>
#include <vector>

class Decimal {
public:
    static constexpr int DEFAULT_PRECISION = 100;

    Decimal();
    explicit Decimal(int64_t v);
    explicit Decimal(const std::string& str);

    // Arithmetic
    Decimal operator+(const Decimal& other) const;
    Decimal operator-(const Decimal& other) const;
    Decimal operator*(const Decimal& other) const;
    Decimal operator/(const Decimal& other) const;
    Decimal operator-() const;
    Decimal& operator+=(const Decimal& other);
    Decimal& operator-=(const Decimal& other);
    Decimal& operator*=(const Decimal& other);
    Decimal& operator/=(const Decimal& other);

    // Comparison
    int compare(const Decimal& other) const;
    bool operator==(const Decimal& other) const;
    bool operator!=(const Decimal& other) const;
    bool operator<(const Decimal& other) const;
    bool operator<=(const Decimal& other) const;
    bool operator>(const Decimal& other) const;
    bool operator>=(const Decimal& other) const;

    // Math
    Decimal sqrt() const;
    Decimal abs() const;

    // Conversions
    std::string toString() const;
    double toDouble() const;
    int64_t toInt64() const;

    // Precision
    void setPrecision(int prec);
    int getPrecision() const { return m_precision; }

    // State
    bool isZero() const;
    bool isNegative() const { return m_negative; }

private:
    std::vector<uint8_t> m_digits; // decimal digits 0-9, most significant first
    int m_scale = 0;               // digits after decimal point
    bool m_negative = false;
    int m_precision = DEFAULT_PRECISION;

    void normalize();
    static void align_scale(Decimal& a, Decimal& b);
    Decimal add_abs(const Decimal& other) const;
    Decimal sub_abs(const Decimal& other) const;
    static Decimal divide_long(const Decimal& num, const Decimal& den, int precision);
    void round_to(int target_scale);
};

std::ostream& operator<<(std::ostream& os, const Decimal& d);
