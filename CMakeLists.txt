cmake_minimum_required(VERSION 3.16)
project(clox-tree-walk CXX)

# C++20 is required
set(CMAKE_CXX_STANDARD 20) 
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_BUILD_TYPE "Debug")

# 设置调试器为 GDB
# set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -DDEBUG")
# set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -DNDEBUG")
# set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -O0")
# set(CMAKE_EXE_LINKER_FLAGS_DEBUG "${CMAKE_EXE_LINKER_FLAGS_DEBUG} -g")
# set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -ggdb")


set(EXECUTABLE_OUTPUT_PATH ${PROJECT_SOURCE_DIR}/build/bin/)
add_subdirectory(src/logger)
add_subdirectory(src/lexer)
add_subdirectory(src/parser)
add_subdirectory(src/interpreter)
file(GLOB SRC_LIST1 ${CMAKE_CURRENT_SOURCE_DIR}/src/utils/*.cpp)
file(GLOB SRC_LIST2 ${CMAKE_CURRENT_SOURCE_DIR}/src/builtins/*.cpp)
file(GLOB SRC_LIST3 ${CMAKE_CURRENT_SOURCE_DIR}/src/internals/*.cpp)
# file(GLOB_RECURSE SRC_LIST ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp) 直接包含使用头文件，没有编译成静态库

include_directories(${PROJECT_SOURCE_DIR}/include)
link_directories(${PROJECT_SOURCE_DIR}/lib)

link_libraries(logger lexer parser interpreter)

add_executable(main main.cpp lox.cpp ${SRC_LIST1} ${SRC_LIST2} ${SRC_LIST3})



 