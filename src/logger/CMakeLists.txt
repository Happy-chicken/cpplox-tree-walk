include_directories(${PROJECT_SOURCE_DIR}/include)

file(GLOB LOGGER_SRC_LIST ${CMAKE_CURRENT_SOURCE_DIR}/*.cpp)

set(LIBRARY_OUTPUT_PATH ${PROJECT_SOURCE_DIR}/lib)

add_library(logger STATIC ${LOGGER_SRC_LIST})