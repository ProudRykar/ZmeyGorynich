add_subdirectory(zmey)

add_executable(zmeygorynych main.cpp)
target_link_libraries(zmeygorynych PRIVATE zmey)
