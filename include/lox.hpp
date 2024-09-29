#ifndef LOX_HPP_
#define LOX_HPP_

#include "RuntimeError.hpp"
#include <string>

using std::string;

class lox {
public:
  static int runScript(int argc, char const *argv[]);

private:
  static void runFile(string path);
  static void runPrompt();
  static void run(string source);
};

#endif // LOX_HPP_
