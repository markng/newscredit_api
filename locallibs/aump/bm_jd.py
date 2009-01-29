#
#   bm_jd.py
#
#   David Janes
#   2008.12.12
#
#	JSON declaration language
#

"""
JD Syntax

	<document> ::= <statement>*
	<statement> ::= <command> ( <word> | <word>:<json> )*
	<command>|<word> ::= [a-zA-Z0-9_]
	<json> ::= ... any valid JSON data ...
"""

import sys
import os
import os.path
import types
import re
import pprint

import bm_text
import bm_io

try:
	import json
except ImportError:
	import simplejson as json

from bm_log import Log

class JDError(Exception): 
	def __init__(self, lineno, line, message, command = None):
		Exception.__init__(self, message)

		self.lineno = lineno
		self.line = line
		self.command = command

	def __str__(self):
		result = "%s: lineno=%d" % ( self.__class__.__name__, self.lineno, )

		if self.command:
			result += ' command=%s' % self.command

		if self.line:
			result += ' line=%s' % repr(self.line)

		extend = self.CustomizeResult()
		if extend:
			result += extend

		if self.message:
			result += ': %s' % self.message

		return	result

	def CustomizeResult(self):
		return	None

class JDUnknownCommandError(JDError):
	pass

class JDSyntaxError(JDError): 
	pass

start_rex = re.compile(r"""
	[\s;]*
	(
		[#].*\n
		|
		(?P<command>
			[a-z0-9_.]+
		)?
		\s*
	)
""", re.I|re.VERBOSE) 

argument_rex = re.compile(r"""
	[\s*]*
	(
		[#].*\n
		|
		(?P<end>;)
		|
		(?P<argument>
			[a-z0-9_]+
		)
		(?P<data>:)?
	)
""", re.I|re.VERBOSE) 

data_rex = re.compile(r"""
	(
		(?P<json>
			(true|false|null)
			|
			[-+0-9"'{[]
		)
		|
		(?P<other>
			[^\s;]+
		)
	)
""", re.I|re.VERBOSE) 

class JDParser():
	"""Base class for JD parsing. You must use a subclass that implements CustomizeProduce"""

	def __init__(self):
		self.state = self._state_start
		self.command = None
		self.arguments = []
		self.decoder = json.JSONDecoder()

	def FeedString(self, value):
		""" ... """
		value = bm_text.toutf8(value)

		self.original = value
		self.current = value

		self.state = self._state_start
		self.command = None
		self.arguments = []

		nstate = None

		while value:
			nstate, nvalue = self.state(value)
			
			if self.current == None:
				self.current = nvalue

			if nvalue == value and nstate == self.state:
				self.RaiseError(JDSyntaxError, message = "Document not completely parsed - may indicate an internal error")
				break

			if not nstate:
				break

			value = nvalue
			self.state = nstate

		if self.command:
			self.RaiseError(JDSyntaxError, message = "Missing ';'")

		if value:
			self.RaiseError(JDSyntaxError, message = "Document not completely parsed - may indicate an internal error")

	def RaiseError(self, cls, message = None, **ad):
		"""Internal function for raising a syntax error"""

		#
		#	Normalize newlines
		#
		original = self.original.replace("\r\n", "\n").replace("\r", "\n")
		current = ( self.current or "" ).replace("\r\n", "\n").replace("\r", "\n")

		#
		#	Find out where the error occurred
		#
		index = len(original) - len(current)

		#
		#	Find out the current line number
		#
		lineno = len(re.sub("[^\n]", "", original[:index])) + 1

		#
		#	Find the current line, up to a newline
		#
		nlx = current.find('\n')
		if nlx == -1:
			nlx = len(current)

		line = current[:nlx]

		#
		#
		#
		raise cls(
			lineno = lineno,
			line = line,
			message = message,
			command = self.command,
			**ad
		)

	def _state_start(self, value):
		Log("START", value = repr(value[:10]) + "...", verbose = True)

		match = start_rex.match(value)
		if not match:
			return	self._state_start, value

		self.command = match.group('command')
		self.arguments = []

		if not self.command:
			self.current = None
			return	self._state_start, value[match.end():]

		return	self._state_argument, value[match.end():]

	def _state_argument(self, value):
		Log("ARGUMENT", value = repr(value[:10]) + "...", verbose = True)

		argument_match = argument_rex.match(value)
		if not argument_match:
			self.RaiseError(JDSyntaxError, message = "Missing ';'")

		if argument_match.group('end'):
			Log("EOS", verbose = True)

			self._produce()
			return	self._state_start, value[argument_match.end():]

		if argument_match.group('argument'):
			if argument_match.group('data'):
				value = value[argument_match.end():]
				data_match = data_rex.match(value)

				if value[:3] in [ '"""', "'''", ]:
					end = value[:3]

					position = 3
					while True:
						endx = value.find(end, position)
						if endx == -1:
							Log("problem, expected end of multiline string, found nothing")
							return	None, value

						if not ( value[endx - 1] == '\\' and value[endx - 2] != '\\' ):
							break

						position = endx + 1

					self.arguments.append(( argument_match.group('argument'), eval(value[:endx + 3]) ))

					return	self._state_argument, value[endx + 3:]
				elif data_match.group('json'):
					try:
						object, index = self.decoder.raw_decode(value)
					except ValueError, x:
						self.RaiseError(JDSyntaxError, message = "command='%s' argument='%s' JSON error: %s" % ( self.command, argument_match.group('argument'), x.message, ))
						
					self.arguments.append(( argument_match.group('argument'), object ))

					return	self._state_argument, value[index:]
				elif data_match.group('other'):
					### ... this isn't quite right, we need a proper path tokenizer
					self.arguments.append(( argument_match.group('argument'), data_match.group('other'), ))
					return	self._state_argument, value[data_match.end():]
			else:
				self.arguments.append(( argument_match.group('argument'), None ))
				return	self._state_argument, value[argument_match.end():]

		return	self._state_argument, value[argument_match.end():]

	def _produce(self):
		Log(command = self.command, arguments = self.arguments, verbose = True)

		if self.command:
			self.CustomizeProduce(self.command, self.arguments)

		self.command = None
		self.current = None
		self.arguments = []

	def CustomizeProduce(self, command, arguments):
		raise	NotImplementedError

class LogJDParser(JDParser):
	"""Log everything parsed. This is for testing"""

	def CustomizeProduce(self, command, arguments):
		Log(
			"PRODUCED",
			command = command,
			arguments = arguments,
		)

class DispatchJDParser(JDParser):
	"""All commands are implemented as methods called call_<command>. If 'call' is implemented it's a catchall"""

	def CustomizeProduce(self, command, arguments):
		ad = dict(arguments)

		fname = "call_%s" % command
		if hasattr(self, fname):
			getattr(self, fname)(**ad)
			return

		self.CustomizeCall(command, **ad)

	def CustomizeCall(self, command, **ad):
		self.RaiseError(JDUnknownCommandError, message = command)

if __name__ == '__main__':
	## Log.verbose = True
	parser = LogJDParser()

	for file in sys.argv[1:]:
		parser.FeedString(bm_io.readfile(file))
