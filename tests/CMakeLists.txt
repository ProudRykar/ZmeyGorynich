add_executable(zmey_tests
    test_main.cpp
    test_decimal.cpp
    test_lexer.cpp
    test_parser.cpp
    test_evaluator.cpp
)

target_link_libraries(zmey_tests PRIVATE zmey Catch2::Catch2WithMain)
target_include_directories(zmey_tests PRIVATE ${CMAKE_SOURCE_DIR}/src/zmey)

include(Catch)
catch_discover_tests(zmey_tests)
