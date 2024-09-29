include_directories(${PROJECT_SOURCE_DIR}/include)

file(GLOB PARSER_SRC_LIST ${CMAKE_CURRENT_SOURCE_DIR}/*.cpp)
set(LIBRARY_OUTPUT_PATH ${PROJECT_SOURCE_DIR}/lib)

add_library(interpreter STATIC ${PARSER_SRC_LIST})

find_library(logger
             NAMES logger
             PATHS ${LIBRARY_OUTPUT_PATH})
target_link_libraries(interpreter PRIVATE ${logger})

