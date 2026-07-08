add_library(zmey
    utf8.cpp
    error.cpp
    decimal.cpp
    token.cpp
    lexer.cpp
    parser.cpp
    value.cpp
    context.cpp
    builtins.cpp
    evaluator.cpp
)

target_include_directories(zmey PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
