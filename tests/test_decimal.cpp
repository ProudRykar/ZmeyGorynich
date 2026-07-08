#include <catch2/catch_test_macros.hpp>
#include "decimal.h"

using namespace std::string_literals;

static Decimal d(int64_t v) { return Decimal(v); }

TEST_CASE("Decimal construction", "[decimal]") {
    SECTION("default") {
        Decimal d0;
        REQUIRE(d0.toString() == "0");
        REQUIRE(d0.isZero());
        REQUIRE_FALSE(d0.isNegative());
    }

    SECTION("from int64_t") {
        Decimal d42(42);
        REQUIRE(d42.toString() == "42");
        REQUIRE_FALSE(d42.isZero());

        Decimal neg(-5);
        REQUIRE(neg.toString() == "-5");
        REQUIRE(neg.isNegative());
    }

    SECTION("from string") {
        REQUIRE(Decimal("123.456").toString() == "123.456");
        REQUIRE(Decimal("0.001").toString() == "0.001");
        REQUIRE(Decimal("-3.14").toString() == "-3.14");
        REQUIRE(Decimal("100").toString() == "100");
        REQUIRE(Decimal("0").toString() == "0");
    }
}

TEST_CASE("Decimal comparison", "[decimal]") {
    REQUIRE(d(5) == d(5));
    REQUIRE_FALSE(d(5) == d(6));
    REQUIRE(d(3) < d(5));
    REQUIRE(d(10) > d(2));
    REQUIRE(d(5) <= d(5));
    REQUIRE(d(5) >= d(5));
    REQUIRE(Decimal("3.14") < Decimal("3.15"));
    REQUIRE(d(-5) < d(0));
    REQUIRE(d(-5) < d(1));
    REQUIRE(d(-2) > d(-5));
}

TEST_CASE("Decimal arithmetic", "[decimal]") {
    SECTION("addition") {
        REQUIRE((d(2) + d(3)).toString() == "5");
        REQUIRE((Decimal("1.5") + Decimal("2.5")).toString() == "4");
        REQUIRE((Decimal("0.1") + Decimal("0.2")).toString() == "0.3");
        REQUIRE((d(-5) + d(3)).toString() == "-2");
        REQUIRE((d(5) + d(-3)).toString() == "2");
    }

    SECTION("subtraction") {
        REQUIRE((d(10) - d(3)).toString() == "7");
        REQUIRE((Decimal("5.5") - Decimal("2.2")).toString() == "3.3");
        REQUIRE((d(3) - d(5)).toString() == "-2");
    }

    SECTION("multiplication") {
        REQUIRE((d(6) * d(7)).toString() == "42");
        REQUIRE((Decimal("2.5") * d(2)).toString() == "5");
        REQUIRE((d(-3) * d(4)).toString() == "-12");
        REQUIRE((d(-2) * d(-3)).toString() == "6");
    }

    SECTION("division") {
        REQUIRE((d(10) / d(2)).toString() == "5");
        REQUIRE((Decimal("7.5") / Decimal("2.5")).toString() == "3");
    }

    SECTION("negation") {
        REQUIRE((-d(5)).toString() == "-5");
        REQUIRE((-d(-3)).toString() == "3");
    }
}

TEST_CASE("Decimal sqrt", "[decimal]") {
    auto r = d(16).sqrt();
    REQUIRE(r.toString() == "4");
    REQUIRE_FALSE(d(2).sqrt().isZero());
}

TEST_CASE("Decimal precision", "[decimal]") {
    Decimal x("1.23456");
    x.setPrecision(2);
    REQUIRE(x.toString() == "1.23");

    Decimal y("9.9999");
    y.setPrecision(2);
    REQUIRE(y.toString() == "10");
}
