#include "decimal.h"
#include <algorithm>
#include <cctype>
#include <cmath>
#include <iostream>
#include <stdexcept>

Decimal::Decimal() {
    m_digits.push_back(0);
    m_scale = 0;
    m_negative = false;
}

Decimal::Decimal(int64_t v) {
    if (v < 0) {
        m_negative = true;
        v = -v;
    }
    if (v == 0) {
        m_digits.push_back(0);
    } else {
        while (v > 0) {
            m_digits.push_back(static_cast<uint8_t>(v % 10));
            v /= 10;
        }
        std::reverse(m_digits.begin(), m_digits.end());
    }
    m_scale = 0;
}

Decimal::Decimal(const std::string& str) {
    size_t pos = 0;
    if (pos < str.size() && str[pos] == '-') {
        m_negative = true;
        pos++;
    } else if (pos < str.size() && str[pos] == '+') {
        pos++;
    }

    // Integer part
    bool found_dot = false;
    bool has_digits = false;
    while (pos < str.size()) {
        char c = str[pos];
        if (c == '.') {
            found_dot = true;
            pos++;
            break;
        }
        if (c >= '0' && c <= '9') {
            m_digits.push_back(static_cast<uint8_t>(c - '0'));
            has_digits = true;
            pos++;
        } else {
            break;
        }
    }

    if (!has_digits) {
        m_digits.push_back(0);
    }

    // Fractional part
    if (found_dot) {
        while (pos < str.size()) {
            char c = str[pos];
            if (c >= '0' && c <= '9') {
                m_digits.push_back(static_cast<uint8_t>(c - '0'));
                m_scale++;
                pos++;
            } else {
                break;
            }
        }
    }

    // Scientific notation
    if (pos < str.size() && (str[pos] == 'e' || str[pos] == 'E')) {
        pos++;
        int exp_sign = 1;
        if (pos < str.size() && str[pos] == '-') {
            exp_sign = -1;
            pos++;
        } else if (pos < str.size() && str[pos] == '+') {
            pos++;
        }
        int exp_val = 0;
        while (pos < str.size() && str[pos] >= '0' && str[pos] <= '9') {
            exp_val = exp_val * 10 + (str[pos] - '0');
            pos++;
        }
        exp_val *= exp_sign;

        // Move the decimal point
        if (exp_val > 0) {
            // Shift right: add zeros to integer part
    int int_digits = (m_scale < static_cast<int>(m_digits.size()))
                     ? static_cast<int>(m_digits.size()) - m_scale
                     : 0;
            while (exp_val > 0 && m_scale > 0) {
                // Move digit from fractional to integer
                exp_val--;
                m_scale--;
            }
            while (exp_val > 0) {
                m_digits.push_back(0);
                exp_val--;
            }
        } else if (exp_val < 0) {
            exp_val = -exp_val;
            while (exp_val > 0 && m_digits.size() > m_scale) {
                // Can move from integer to fractional
                exp_val--;
                m_scale++;
            }
            while (exp_val > 0) {
                m_digits.insert(m_digits.begin(), 0);
                m_scale++;
                exp_val--;
            }
        }
    }

    normalize();
}

void Decimal::normalize() {
    if (m_digits.empty()) {
        m_digits.push_back(0);
        m_scale = 0;
        m_negative = false;
        return;
    }

    // Remove leading zeros from the integer part, but keep at least one digit.
    int int_digits = (m_scale < static_cast<int>(m_digits.size()))
                     ? static_cast<int>(m_digits.size()) - m_scale
                     : 0;
    int removable = 0;
    while (removable < int_digits && m_digits[removable] == 0) {
        ++removable;
    }
    if (removable == int_digits && int_digits > 0) {
        // All integer digits were zero — keep one zero as integer part
        removable = int_digits - 1;
    }
    if (removable > 0) {
        m_digits.erase(m_digits.begin(), m_digits.begin() + removable);
    }

    // Remove trailing zeros from fractional part
    while (m_scale > 0 && !m_digits.empty() && m_digits.back() == 0) {
        m_digits.pop_back();
        m_scale--;
    }

    if (m_digits.empty()) {
        m_digits.push_back(0);
        m_scale = 0;
        m_negative = false;
    }
}

void Decimal::align_scale(Decimal& a, Decimal& b) {
    while (a.m_scale < b.m_scale) {
        a.m_digits.push_back(0);
        a.m_scale++;
    }
    while (b.m_scale < a.m_scale) {
        b.m_digits.push_back(0);
        b.m_scale++;
    }
}

int Decimal::compare(const Decimal& other) const {
    if (m_negative != other.m_negative) {
        return m_negative ? -1 : 1;
    }

    Decimal a = *this;
    Decimal b = other;
    align_scale(a, b);

    // Equalize lengths
    while (a.m_digits.size() < b.m_digits.size()) {
        a.m_digits.insert(a.m_digits.begin(), 0);
    }
    while (b.m_digits.size() < a.m_digits.size()) {
        b.m_digits.insert(b.m_digits.begin(), 0);
    }

    for (size_t i = 0; i < a.m_digits.size(); ++i) {
        if (a.m_digits[i] != b.m_digits[i]) {
            int cmp = (a.m_digits[i] < b.m_digits[i]) ? -1 : 1;
            bool both_neg = m_negative && other.m_negative;
            return both_neg ? -cmp : cmp;
        }
    }
    return 0;
}

bool Decimal::operator==(const Decimal& other) const { return compare(other) == 0; }
bool Decimal::operator!=(const Decimal& other) const { return compare(other) != 0; }
bool Decimal::operator<(const Decimal& other) const { return compare(other) < 0; }
bool Decimal::operator<=(const Decimal& other) const { return compare(other) <= 0; }
bool Decimal::operator>(const Decimal& other) const { return compare(other) > 0; }
bool Decimal::operator>=(const Decimal& other) const { return compare(other) >= 0; }

Decimal Decimal::operator-() const {
    Decimal result = *this;
    if (!result.isZero()) {
        result.m_negative = !result.m_negative;
    }
    return result;
}

Decimal Decimal::abs() const {
    Decimal result = *this;
    result.m_negative = false;
    return result;
}

bool Decimal::isZero() const {
    return m_digits.size() == 1 && m_digits[0] == 0;
}

Decimal Decimal::operator+(const Decimal& other) const {
    if (m_negative == other.m_negative) {
        // Same sign: add absolute values
        Decimal a = *this;
        Decimal b = other;
        a.m_negative = false;
        b.m_negative = false;
        Decimal result = a.add_abs(b);
        result.m_negative = m_negative;
        result.m_precision = std::max(m_precision, other.m_precision);
        return result;
    }
    // Different signs: subtract
    Decimal a = *this;
    Decimal b = other;
    a.m_negative = false;
    b.m_negative = false;

    if (a.compare(b) >= 0) {
        Decimal result = a.sub_abs(b);
        result.m_negative = m_negative;
        result.m_precision = std::max(m_precision, other.m_precision);
        return result;
    } else {
        Decimal result = b.sub_abs(a);
        result.m_negative = other.m_negative;
        result.m_precision = std::max(m_precision, other.m_precision);
        return result;
    }
}

Decimal Decimal::operator-(const Decimal& other) const {
    return *this + (-other);
}

Decimal& Decimal::operator+=(const Decimal& other) {
    *this = *this + other;
    return *this;
}

Decimal& Decimal::operator-=(const Decimal& other) {
    *this = *this - other;
    return *this;
}

Decimal Decimal::add_abs(const Decimal& other) const {
    Decimal a = *this;
    Decimal b = other;
    align_scale(a, b);

    // Equalize lengths
    while (a.m_digits.size() < b.m_digits.size()) {
        a.m_digits.insert(a.m_digits.begin(), 0);
    }
    while (b.m_digits.size() < a.m_digits.size()) {
        b.m_digits.insert(b.m_digits.begin(), 0);
    }

    Decimal result;
    result.m_digits.clear();
    result.m_scale = a.m_scale;

    int carry = 0;
    for (int i = static_cast<int>(a.m_digits.size()) - 1; i >= 0; --i) {
        int sum = a.m_digits[i] + b.m_digits[i] + carry;
        result.m_digits.push_back(static_cast<uint8_t>(sum % 10));
        carry = sum / 10;
    }
    if (carry > 0) {
        result.m_digits.push_back(static_cast<uint8_t>(carry));
    }

    std::reverse(result.m_digits.begin(), result.m_digits.end());
    result.normalize();
    result.m_precision = std::max(m_precision, other.m_precision);
    return result;
}

Decimal Decimal::sub_abs(const Decimal& other) const {
    // Assumes |this| >= |other|
    Decimal a = *this;
    Decimal b = other;
    align_scale(a, b);

    while (a.m_digits.size() < b.m_digits.size()) {
        a.m_digits.insert(a.m_digits.begin(), 0);
    }
    while (b.m_digits.size() < a.m_digits.size()) {
        b.m_digits.insert(b.m_digits.begin(), 0);
    }

    Decimal result;
    result.m_digits.clear();
    result.m_scale = a.m_scale;

    int borrow = 0;
    for (int i = static_cast<int>(a.m_digits.size()) - 1; i >= 0; --i) {
        int diff = static_cast<int>(a.m_digits[i]) - static_cast<int>(b.m_digits[i]) - borrow;
        if (diff < 0) {
            diff += 10;
            borrow = 1;
        } else {
            borrow = 0;
        }
        result.m_digits.push_back(static_cast<uint8_t>(diff));
    }

    std::reverse(result.m_digits.begin(), result.m_digits.end());
    result.normalize();
    result.m_precision = std::max(m_precision, other.m_precision);
    return result;
}

Decimal Decimal::operator*(const Decimal& other) const {
    Decimal a = *this;
    Decimal b = other;
    a.m_negative = false;
    b.m_negative = false;

    int total_scale = a.m_scale + b.m_scale;

    // LSD-first digit vectors
    std::vector<uint8_t> a_lsd(a.m_digits.rbegin(), a.m_digits.rend());
    std::vector<uint8_t> b_lsd(b.m_digits.rbegin(), b.m_digits.rend());

    std::vector<uint8_t> result(a_lsd.size() + b_lsd.size() + 1, 0);

    for (size_t i = 0; i < a_lsd.size(); ++i) {
        int carry = 0;
        for (size_t j = 0; j < b_lsd.size(); ++j) {
            int prod = a_lsd[i] * b_lsd[j] + result[i + j] + carry;
            result[i + j] = static_cast<uint8_t>(prod % 10);
            carry = prod / 10;
        }
        if (carry > 0) {
            result[i + b_lsd.size()] += static_cast<uint8_t>(carry);
        }
    }

    // Remove trailing zeros (LSD) and convert to MSD-first
    while (!result.empty() && result.back() == 0) {
        result.pop_back();
    }
    std::reverse(result.begin(), result.end());
    if (result.empty()) result.push_back(0);

    Decimal r;
    r.m_digits = result;
    r.m_scale = total_scale;
    r.m_negative = m_negative != other.m_negative;
    r.m_precision = std::max(m_precision, other.m_precision);
    r.normalize();
    return r;
}

Decimal& Decimal::operator*=(const Decimal& other) {
    *this = *this * other;
    return *this;
}

Decimal Decimal::operator/(const Decimal& other) const {
    if (other.isZero()) {
        throw std::runtime_error("Division by zero");
    }
    if (isZero()) {
        return Decimal();
    }

    int target_precision = std::max(m_precision, other.m_precision) + 5; // extra for rounding
    Decimal result = divide_long(*this, other, target_precision);
    result.m_precision = std::max(m_precision, other.m_precision);

    // Trim trailing zeros
    while (result.m_scale > 0 && !result.m_digits.empty() && result.m_digits.back() == 0) {
        result.m_digits.pop_back();
        result.m_scale--;
    }
    result.normalize();
    result.round_to(std::max(m_precision, other.m_precision));

    return result;
}

Decimal& Decimal::operator/=(const Decimal& other) {
    *this = *this / other;
    return *this;
}

Decimal Decimal::divide_long(const Decimal& num, const Decimal& den, int precision) {
    Decimal dividend = num;
    Decimal divisor = den;
    dividend.m_negative = false;
    divisor.m_negative = false;

    // Align scales
    align_scale(dividend, divisor);

    // Remove decimal points to work with integers
    auto a_digits = dividend.m_digits;
    auto b_digits = divisor.m_digits;

    // Add 'precision' fractional zeros to dividend
    for (int i = 0; i < precision; ++i) {
        a_digits.push_back(0);
    }

    // Do integer long division of a_digits / b_digits
    std::vector<uint8_t> quotient;
    std::vector<uint8_t> remainder; // current partial dividend

    // Helper: compare two digit vectors (MSD-first)
    auto cmp_vec = [](const std::vector<uint8_t>& a, const std::vector<uint8_t>& b) -> int {
        // Skip leading zeros
        size_t ai = 0, bi = 0;
        while (ai < a.size() && a[ai] == 0) ai++;
        while (bi < b.size() && b[bi] == 0) bi++;
        size_t alen = a.size() - ai;
        size_t blen = b.size() - bi;
        if (alen != blen) return alen < blen ? -1 : 1;
        for (size_t k = 0; k < alen; ++k) {
            uint8_t va = a[ai + k];
            uint8_t vb = b[bi + k];
            if (va != vb) return va < vb ? -1 : 1;
        }
        return 0;
    };

    // Helper: subtract b from a (a >= b), store in a, return borrow
    auto sub_vec = [](std::vector<uint8_t>& a, const std::vector<uint8_t>& b) {
        // Pad a and b to same length
        while (a.size() < b.size()) a.insert(a.begin(), 0);
        // Do subtraction LSD-first
        int borrow = 0;
        for (int i = static_cast<int>(a.size()) - 1; i >= 0; --i) {
            int b_digit = (i >= static_cast<int>(b.size())) ? 0 : b[i];
            int diff = static_cast<int>(a[i]) - b_digit - borrow;
            if (diff < 0) {
                diff += 10;
                borrow = 1;
            } else {
                borrow = 0;
            }
            a[i] = static_cast<uint8_t>(diff);
        }
    };

    // Helper: multiply b by d (single digit), return product
    auto mul_vec = [](const std::vector<uint8_t>& b, int d) -> std::vector<uint8_t> {
        std::vector<uint8_t> prod;
        int carry = 0;
        for (int i = static_cast<int>(b.size()) - 1; i >= 0; --i) {
            int p = b[i] * d + carry;
            prod.push_back(static_cast<uint8_t>(p % 10));
            carry = p / 10;
        }
        if (carry > 0) {
            prod.push_back(static_cast<uint8_t>(carry));
        }
        std::reverse(prod.begin(), prod.end());
        return prod;
    };

    for (size_t pos = 0; pos < a_digits.size(); ++pos) {
        // Append next digit to remainder
        remainder.push_back(a_digits[pos]);

        // Skip leading zeros in remainder
        auto it = remainder.begin();
        while (it != remainder.end() && *it == 0) ++it;
        std::vector<uint8_t> remainder_trimmed(it, remainder.end());
        if (remainder_trimmed.empty()) {
            quotient.push_back(0);
            remainder = {0};  // keep as 0 for next iteration
            continue;
        }

        int q_digit = 0;
        if (cmp_vec(remainder, b_digits) >= 0) {
            // Try 1..9
            for (int d = 1; d <= 9; ++d) {
                auto prod = mul_vec(b_digits, d);
                if (cmp_vec(prod, remainder) > 0) {
                    break;
                }
                q_digit = d;
            }
            // Subtract divisor * q_digit from remainder
            if (q_digit > 0) {
                auto prod = mul_vec(b_digits, q_digit);
                sub_vec(remainder, prod);
                // Remove leading zeros from remainder
                auto it2 = remainder.begin();
                while (it2 != remainder.end() && *it2 == 0) ++it2;
                if (it2 == remainder.end()) {
                    remainder = {0};
                } else if (it2 != remainder.begin()) {
                    remainder.erase(remainder.begin(), it2);
                }
            }
        } else {
            // Nothing to do, q_digit stays 0
        }

        quotient.push_back(static_cast<uint8_t>(q_digit));
    }

    // Build result
    Decimal result;
    result.m_digits = quotient;
    result.m_scale = precision;
    result.m_negative = num.m_negative != den.m_negative;
    result.normalize();

    // Trim trailing zeros from fractional part
    while (result.m_scale > 0 && !result.m_digits.empty() && result.m_digits.back() == 0) {
        result.m_digits.pop_back();
        result.m_scale--;
    }
    result.normalize();

    return result;
}

Decimal Decimal::sqrt() const {
    if (m_negative) {
        throw std::runtime_error("Square root of negative number");
    }
    if (isZero()) {
        return Decimal();
    }

    int target_precision = m_precision + 2;
    
    // Newton's method: x_{n+1} = (x_n + a/x_n) / 2
    Decimal a = *this;
    Decimal two(static_cast<int64_t>(2));
    
    // Initial guess: a / 2 (but at least 1)
    Decimal x;
    if (a > Decimal(static_cast<int64_t>(1))) {
        x = a / two;
    } else {
        x = a;
    }

    for (int iter = 0; iter < 20; ++iter) {
        Decimal next = (x + a / x) / two;
        next.setPrecision(target_precision);
        if (next == x) {
            x = next;
            break;
        }
        x = next;
    }

    x.setPrecision(m_precision);
    return x;
}

void Decimal::setPrecision(int prec) {
    if (prec < 0) prec = 0;
    m_precision = prec;
    round_to(prec);
}

void Decimal::round_to(int target_scale) {
    if (target_scale < 0 || m_scale <= target_scale) return;

    int digits_to_remove = m_scale - target_scale;

    // The digit at this index determines rounding (first digit to be removed)
    size_t round_idx = m_digits.size() - digits_to_remove;
    uint8_t round_digit = m_digits[round_idx];

    // Remove excess digits
    m_digits.erase(m_digits.end() - digits_to_remove, m_digits.end());
    m_scale = target_scale;

    // Round up if needed
    if (round_digit >= 5) {
        int i = static_cast<int>(m_digits.size()) - 1;
        while (i >= 0 && m_digits[i] == 9) {
            m_digits[i] = 0;
            i--;
        }
        if (i >= 0) {
            m_digits[i]++;
        } else {
            m_digits.insert(m_digits.begin(), 1);
        }
    }

    normalize();
}

std::string Decimal::toString() const {
    if (m_digits.empty()) {
        return "0";
    }

    std::string result;
    if (m_negative) {
        result += '-';
    }

    size_t int_digits = m_digits.size() - m_scale;

    // Integer part
    if (int_digits == 0) {
        result += '0';
    } else {
        for (size_t i = 0; i < int_digits; ++i) {
            result += static_cast<char>('0' + m_digits[i]);
        }
    }

    // Fractional part
    if (m_scale > 0) {
        result += '.';
        for (int i = 0; i < m_scale; ++i) {
            size_t idx = int_digits + i;
            result += static_cast<char>('0' + (idx < m_digits.size() ? m_digits[idx] : 0));
        }
    }

    return result;
}

double Decimal::toDouble() const {
    std::string s = toString();
    return std::stod(s);
}

int64_t Decimal::toInt64() const {
    std::string s = toString();
    size_t dot = s.find('.');
    if (dot != std::string::npos) {
        s = s.substr(0, dot);
    }
    return std::stoll(s);
}

std::ostream& operator<<(std::ostream& os, const Decimal& d) {
    os << d.toString();
    return os;
}
