
#include <stdexcept>
#include <map>
#include <string>

#include "../../include/Environment.hpp"
#include "../../include/RuntimeError.hpp"

using std::map;
using std::string;

Environment::Environment(shared_ptr<Environment> enclosing_) : enclosing(enclosing_) {}

void Environment::define(string name, Object value)
{
	values[name] = value;
}

Object Environment::get(Token name)
{
	if (values.contains(name.lexeme))
	{
		return values.at(name.lexeme);
	}
	if (enclosing)
	{
		return enclosing->get(name);
	}
	throw RuntimeError(name, "Undefined variable '" + name.lexeme + "'.");
}

Object Environment::getAt(int distance, string name)
{
	return ancestor(distance)->values[name];
}

void Environment::assign(Token name, Object value)
{
	if (values.contains(name.lexeme))
	{
		values[name.lexeme] = value;
		return;
	}
	if (enclosing != nullptr)
	{
		enclosing->assign(name, value);
		return;
	}

	throw RuntimeError(name, "Undefined variable '" + name.lexeme + "'.");
}

void Environment::assignAt(int distance, Token name, Object value)
{
	ancestor(distance)->values[name.lexeme] = value;
}

shared_ptr<Environment> Environment::ancestor(int distance)
{
	shared_ptr<Environment> environment = shared_from_this();
	for (int i = 0; i < distance; i++)
	{
		environment = environment->enclosing;
	}
	return environment;
}