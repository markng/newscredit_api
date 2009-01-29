#
#	djolt.py
#	- djolt - Django-like templates

#	2008-11-18
#
#	External contribution:
#	- see http://effbot.org/zone/simple-top-down-parsing.htm
#

import sys
import re

from bm_log import Log

ID_LITERAL = '(literal)'
ID_LITERAL_NUMBER = '(number)'
ID_LITERAL_STRING = '(string)'
ID_LITERAL_TRUE = '(true)'
ID_LITERAL_FALSE = '(false)'
ID_LITERAL_NONE = '(null)'
ID_NAME = '(name)'
ID_OPERATOR = '(operator)'
ID_END = '(end)'

def is_literal(id):
	return	id in [ ID_LITERAL, ID_LITERAL_NUMBER, ID_LITERAL_STRING, ID_LITERAL_TRUE, ID_LITERAL_FALSE, ID_LITERAL_NONE ]

class symbol_base(object):
	id = None
	value = None
	first = second = third = None

	def nud(self):
		raise SyntaxError("Syntax error (%r)." % self.id)

	def led(self, left):
		raise SyntaxError("Unknown operator (%r)." % self.id)

	def __repr__(self):
		if self.id == ID_NAME or is_literal(self.id):
			return "(%s %s)" % (self.id[1:-1], self.value)

		out = [self.id, self.first, self.second, self.third]
		out = map(str, filter(None, out))
		return "(" + " ".join(out) + ")"

	def Literal(self, context):
		if self.id == ID_NAME:
			return	self.value
		elif self.id == ID_LITERAL_STRING:
			return	self.value
		elif self.id == ID_LITERAL_NUMBER:
			return	self.value
		elif self.id == ID_LITERAL_TRUE:
			return	"True"
		elif self.id == ID_LITERAL_FALSE:
			return	"False"
		elif self.id == ID_LITERAL_NONE:
			return	"None"
		elif self.id == '.':
			return	"%s.%s" % ( self.first.Literal(context), self.second.Literal(context), )
		elif self.id == '[':
			return	"%s[%s]" % ( self.first.Literal(context), self.second.Literal(context), )
		else:
			raise	NotImplementedError, self.id

	def Execute(self, context):
		import bm_extract

		id = self.id
		if id == ID_NAME:
			## Log("HERE:B", value = self.value, result = context.get(self.value))
			return	context.get(self.value)
		elif id == ID_LITERAL_STRING:
			return	self.value
		elif id == ID_LITERAL_NUMBER:
			if self.value.find('.') > -1:
				return	bm_extract.coerce_float(self.value)
			else:
				return	bm_extract.coerce_int(self.value)
		elif id == ID_LITERAL_TRUE:
			return	True
		elif id == ID_LITERAL_FALSE:
			return	False
		elif id == ID_LITERAL_NONE:
			return	False
		elif id == '==':
			return	self.first.Execute(context) == self.second.Execute(context)
		elif id == '!=':
			return	self.first.Execute(context) != self.second.Execute(context)
		elif id == '<':
##			Log("HERE:XXX",
##				first = self.first.Execute(context),
##				second = self.second.Execute(context),
##			)
			return	self.first.Execute(context) < self.second.Execute(context)
		elif id == '<=':
			return	self.first.Execute(context) <= self.second.Execute(context)
		elif id == '>':
			return	self.first.Execute(context) > self.second.Execute(context)
		elif id == '>=':
			return	self.first.Execute(context) >= self.second.Execute(context)
		elif id == '+':
			if self.second == None:
				return	self.first.Execute(context)

			return	self.first.Execute(context) + self.second.Execute(context)
		elif id == '-':
			if self.second == None:
				return	-self.first.Execute(context)

			return	self.first.Execute(context) - self.second.Execute(context)
		elif id == '.':
			## key = "%s.%s" % ( self.first.Literal(context), self.second.Literal(context), )
			## value = context.get(key)
			## print "<%s>/<%s>" % ( key, value )
			return	context.get("%s.%s" % ( self.first.Literal(context), self.second.Literal(context), ))
		elif id == '[':
			## key = "%s[%s]" % ( self.first.Literal(context), self.second.Literal(context), )
			## value = context.get(key)
			## print >> sys.stderr, "!!! <%s>/<%s>" % ( key, value )
			return	context.get("%s[%s]" % ( self.first.Literal(context), self.second.Literal(context), ))
		elif id == 'and':
			a = bm_extract.coerce_bool(self.first.Execute(context))
			b = bm_extract.coerce_bool(self.second.Execute(context))

			return	a and b
		elif id == 'or':
			a = bm_extract.coerce_bool(self.first.Execute(context))
			b = bm_extract.coerce_bool(self.second.Execute(context))

			return	a or b
		elif id == 'not':
			a = bm_extract.coerce_bool(self.first.Execute(context))

			return	not a
		elif id == '(':
			if len(self.second) != 1:
				raise	NotImplementedError, self.id + ": functions take exactly one argument"

			if self.first.value == "int":
				b = bm_extract.coerce_int(self.second[0].Execute(context))
				## Log("HERE:A", b = b, first = self.first, second = self.second[0], valuewas = self.second[0].Execute(context))
			elif self.first.value == "string":
				b = bm_extract.coerce_string(self.second[0].Execute(context))
			elif self.first.value == "bool":
				b = bm_extract.coerce_bool(self.second[0].Execute(context))
			elif self.first.value == "float":
				b = bm_extract.coerce_float(self.second[0].Execute(context))
			else:
				raise	NotImplementedError, self.id + ": function can only be int|string|bool|float"

			return	b
		else:
			print self.id, self.first, self.second, self.third
			raise	NotImplementedError, self.id

# symbol (token type) registry
symbol_table = {}

def symbol(id, bp=0):
	try:
		s = symbol_table[id]
	except KeyError:
		class s(symbol_base):
			pass
		s.__name__ = "symbol-" + id # for debugging
		s.id = id
		s.value = None
		s.lbp = bp
		symbol_table[id] = s
	else:
		s.lbp = max(bp, s.lbp)
	return s

# helpers

def infix(id, bp):
	def led(self, left):
		self.first = left
		self.second = expression(bp)
		return self
	symbol(id, bp).led = led

def infix_r(id, bp):
	def led(self, left):
		self.first = left
		self.second = expression(bp-1)
		return self
	symbol(id, bp).led = led

def prefix(id, bp):
	def nud(self):
		self.first = expression(bp)
		return self
	symbol(id).nud = nud

def advance(id=None):
	global token
	if id and token.id != id:
		raise SyntaxError("Expected %r" % id)
	token = next()

def method(s):
	# decorator
	assert issubclass(s, symbol_base)
	def bind(fn):
		setattr(s, fn.__name__, fn)
	return bind

# python expression syntax

symbol("lambda", 20)
symbol("if", 20); symbol("else") # ternary form

infix_r("or", 30); infix_r("and", 40); prefix("not", 50)

infix("in", 60); infix("not", 60) # not in
infix("is", 60);
infix("<", 60); infix("<=", 60)
infix(">", 60); infix(">=", 60)
infix("<>", 60); infix("!=", 60); infix("==", 60)

infix("|", 70); infix("^", 80); infix("&", 90)

infix("<<", 100); infix(">>", 100)

infix("+", 110); infix("-", 110)

infix("*", 120); infix("/", 120); infix("//", 120)
infix("%", 120)

prefix("-", 130); prefix("+", 130); prefix("~", 130)

infix_r("**", 140)

symbol(".", 150); symbol("[", 150); symbol("(", 150)

# additional behaviour

symbol(ID_NAME).nud = lambda self: self
symbol(ID_LITERAL).nud = lambda self: self
symbol(ID_LITERAL_NUMBER).nud = lambda self: self
symbol(ID_LITERAL_STRING).nud = lambda self: self
symbol(ID_LITERAL_TRUE, "True").nud = lambda self: self
symbol(ID_LITERAL_FALSE, "False").nud = lambda self: self
symbol(ID_LITERAL_NONE, "None").nud = lambda self: self
# constants

#	def constant(id):
#		@method(symbol(id))
#		def nud(self):
#			self.id = ID_LITERAL
#			self.value = id
#			return self
#
#	constant("None")
#	constant("True")
#	constant("False")


symbol(ID_END)

symbol(")")

@method(symbol("("))
def nud(self):
	# parenthesized form; replaced by tuple former below
	expr = expression()
	advance(")")
	return expr

symbol("else")

@method(symbol("if"))
def led(self, left):
	self.first = left
	self.second = expression()
	advance("else")
	self.third = expression()
	return self

@method(symbol("."))
def led(self, left):
	if token.id != ID_NAME:
		SyntaxError("Expected an attribute name.")
	self.first = left
	self.second = token
	advance()
	return self

symbol("]")

@method(symbol("["))
def led(self, left):
	self.first = left
	self.second = expression()
	advance("]")
	return self

symbol(")"); symbol(",")

@method(symbol("("))
def led(self, left):
	self.first = left
	self.second = []
	if token.id != ")":
		while 1:
			self.second.append(expression())
			if token.id != ",":
				break
			advance(",")
	advance(")")
	return self

symbol(":"); symbol("=")

@method(symbol("lambda"))
def nud(self):
	self.first = []
	if token.id != ":":
		argument_list(self.first)
	advance(":")
	self.second = expression()
	return self

def argument_list(list):
	while 1:
		if token.id != ID_NAME:
			SyntaxError("Expected an argument name.")
		list.append(token)
		advance()
		if token.id == "=":
			advance()
			list.append(expression())
		else:
			list.append(None)
		if token.id != ",":
			break
		advance(",")

# multitoken operators

@method(symbol("not"))
def led(self, left):
	if token.id != "in":
		raise SyntaxError("Invalid syntax")
	advance()
	self.id = "not in"
	self.first = left
	self.second = expression(60)
	return self

@method(symbol("is"))
def led(self, left):
	if token.id == "not":
		advance()
		self.id = "is not"
	self.first = left
	self.second = expression(60)
	return self

# displays

@method(symbol("("))
def nud(self):
	self.first = []
	comma = False
	if token.id != ")":
		while 1:
			if token.id == ")":
				break
			self.first.append(expression())
			if token.id != ",":
				break
			comma = True
			advance(",")
	advance(")")
	if not self.first or comma:
		return self # tuple
	else:
		return self.first[0]

symbol("]")

@method(symbol("["))
def nud(self):
	self.first = []
	if token.id != "]":
		while 1:
			if token.id == "]":
				break
			self.first.append(expression())
			if token.id != ",":
				break
			advance(",")
	advance("]")
	return self

symbol("}")

@method(symbol("{"))
def nud(self):
	self.first = []
	if token.id != "}":
		while 1:
			if token.id == "}":
				break
			self.first.append(expression())
			advance(":")
			self.first.append(expression())
			if token.id != ",":
				break
			advance(",")
	advance("}")
	return self

# python tokenizer

def tokenize_python(program):
	import tokenize
	from StringIO import StringIO
	type_map = {
		tokenize.NUMBER: ID_LITERAL_NUMBER,
		tokenize.STRING: ID_LITERAL_STRING,
		tokenize.OP: ID_OPERATOR,
		tokenize.NAME: ID_NAME,
		"true" : ID_LITERAL_TRUE,
		"false" : ID_LITERAL_FALSE,
		"null" : ID_LITERAL_NONE,
		"True" : ID_LITERAL_TRUE,
		"False" : ID_LITERAL_FALSE,
		"None" : ID_LITERAL_NONE,
		}
	for t in tokenize.generate_tokens(StringIO(program).next):
		## Log("HERE:F", t = t, program = repr(program))
		try:
			if t[0] == tokenize.NAME and type_map.get(t[1]):
				yield type_map[t[1]], t[1]

			if t[0] == tokenize.STRING:
				t = ( t[0],  eval(t[1]) )
					
			## Log("HERE:F.2")
			yield type_map[t[0]], t[1]
		except KeyError:
			if t[0] == tokenize.NL:
				continue
			if t[0] == tokenize.ENDMARKER:
				break
			else:
				raise SyntaxError("Syntax error", t)

	yield ID_END, ID_END

def tokenize(program):
	if isinstance(program, list):
		## Log("HERE:E.LIST")
		source = program
	else:
		## Log("HERE:E.TEXT", program = program)
		source = tokenize_python(program)
	## Log("HERE:E", source = source, program = program)
	for id, value in source:
		## Log("HERE:E.1", id = id, value = value)
		if is_literal(id):
			symbol = symbol_table[id]
			s = symbol()
			s.value = value
		else:
			# name or operator
			symbol = symbol_table.get(value)
			if symbol:
				s = symbol()
			elif id == ID_NAME:
				symbol = symbol_table[id]
				s = symbol()
				s.value = value
			else:
				raise SyntaxError("Unknown operator (%r)" % id)
		yield s

# parser engine

def expression(rbp=0):
	global token
	t = token
	token = next()
	left = t.nud()
	while rbp < token.lbp:
		t = token
		token = next()
		left = t.led(left)
	return left

def parse(program):
	## Log("HERE:D.1", program = program)
	global token, next
	token = None
	next = None
	next = tokenize(program).next
	token = next()
	return expression()

def test(program):
	print ">>>", program
	print parse(program)

if __name__ == '__main__':
	def test1():
		test("1")
		test("+1")
		test("-1")
		test("1+2")
		test("1+2+3")
		test("1+2*3")
		test("(1+2)*3")
		test("()")
		test("(1)")
		test("(1,)")
		test("(1, 2)")
		test("[1, 2, 3]")
		test("{}")
		test("{1: 'one', 2: 'two'}")
		test("1.0*2+3")
		test("'hello'+'world'")
		test("2**3**4")
		test("1 and 2")
		test("foo.bar")
		test("1 + hello")
		test("1 if 2 else 3")
		test("'hello'[0]")
		test("hello()")
		test("hello(1,2,3)")
		test("lambda: 1")
		test("lambda a, b, c: a+b+c")
		test("True")
		test("True or False")
		test("1 in 2")
		test("1 not in 2")
		test("1 is 2")
		test("1 is not 2")
		test("1 is (not 2)")

		print
		print list(tokenize("1 not in 2"))

	def test2():
		import djolt
		context = djolt.Context({
			"a" : 17,
			"b" : 37,
			"c" : "David",
			"x" : {
				"a" : 1,
				"b" : 2,
				"c" : 3,
				"d" : 1,
				"e" : {
					"x" : 1,
					"y" : [ 4, 3, 2, 1, 0 ],
				}
			}
		})

		programs = [
			"a + 1",
			"b - a",
			"a == 'David'",
			"b == 'David Janes'",
			"c == 'David'",
			"c == 'David Janes'",
			"'David Janes'",
			"a",
			"b",
			"c",
			"x.a == x.d",
			"x.a == x.b",
			"x.a == x.e",
			"x.a == x.e.x",
			"x.a == x.e.y[0]",
			"x.a == x.e.y[1]",
			"x.a == x.e.y[2]",
			"x.a == x.e.y[3]",
			"x.a == x.e.y[4]",
		]
		xprograms = [
			"'David Janes'",
		]
		programs = [
			"a < 0",
			"int(a) < 0",
			"int(a)",
			"bool(a)",
			"int(ticker) > 0",
			"int(ticker) < 0",
			"int(ticker) == 0",
		]
		programs = [
			"true",
			"True"
		]

		for program in programs:
			expr = parse(program)
			print "%s: <%s>" % ( program, expr.Execute(context), )

	def test3():
		programs = [
			"x",
			"x.y",
			"x.y[3]",
			"x.y[3].z",
		]
		for program in programs:
			print parse(program)

	test2()
