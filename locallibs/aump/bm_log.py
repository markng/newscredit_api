#
#   bm_io.py
#
#   David Janes
#	2005.01.01
#
#	A powerful logging function
#

import sys
import traceback
import thread
import time
import inspect
import pprint
import types
import cStringIO
import os
import os.path

# this is for people outside of the BlogMatrix environment
try:
	import bm_config
except ImportError:
	bm_config = None

debugging = {}
time_format = os.getenv("BM_LOG_FORMAT", "%x %X")
ignore_severity = eval( os.getenv( "BM_LOG_SEVERITY_IGNORE", "[ 'debug' , 'info' ]" ) )

#
# Severity levels: debug, info, warning, error, critical
#

def Log(_message = "", exception = False, logfile = None, logdir = None, severity="info", verbose = None, **args):
	""" Log a message: logdir and severity are synonyms, recomended severities are:
	    debug, info, warning, error, critical
	"""
	if verbose and not Log.verbose:
		return

	result = ""

	debug = args.get('debug')
	if severity not in ignore_severity :
		logdir = logdir or severity
	if type(debug) not in [ types.NoneType, types.IntType, types.BooleanType ]:
		debug = debugging.get(debug, False)
	if debug == False:
		return

	try:
		cout = cStringIO.StringIO()
		print >> cout, "[log_entry]"
		if logdir and os.path.exists( logdir ) :
			print >> cout, "[severity]", severity
		else :
			print >> cout, "[severity]", logdir or severity
		print >> cout, "[date]", time.strftime( time_format )
		try:
			caller = inspect.stack()[1]
			if debug == True:
				if bm_config and bm_config.cfg:
					cfg_debug = bm_config.cfg

					module_name = os.path.basename(caller[1]).rstrip(".py")
					function_name = caller[3].lstrip("_")

					module = cfg_debug.get( module_name )
					try: v = module.get( function_name )
					except: v = None

					if v != None:
						if v == False:
							return
					else:
						## debug["Module"] -- control on a per module basis
						v = cfg_debug.get(module_name)
						if v == False:
							return

			print >> cout, "%s (%s:%d)" % ( caller[3], caller[1], caller[2], )
		except IndexError:
			pass
		except:
			print >> cout, "(exception gettings stack)"
			traceback.print_exc()

		if _message:
			print >> cout, "  message: %s" % ( _message, )

		items = args.items()
		items.sort()

		if exception:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			items.append(("traceback-type", exc_type))
			items.append(("traceback-value", exc_value))
			items.append(("traceback-stack", traceback.extract_tb(exc_traceback)))

		if args.get("stack_trace"):
			stack = inspect.stack()
			for frame in stack:
				print >> cout, "  %s (%s:%d)" % ( frame[3],  frame[1], frame[2], )

		for key, value in items:
			if isinstance(value, ( dict, list)):
				print >> cout, "  %s:" % ( key, )
				for line in pprint.pformat(value).split("\n"):
					print >> cout, "   ", line
			elif type(value) in types.StringTypes and value.find("\n") > -1:
				print >> cout, "  %s: ---" % ( key, )
				for line in value.split("\n"):
					if type(line) == types.UnicodeType:
						print >> cout, ".  %s" % ( line.encode('latin-1', 'replace') )
					else:
						print >> cout, ".  %s" % ( line )
				print >> cout, "  -------"
			elif type(value) == types.UnicodeType:
				print >> cout, "  %s: %s" % ( key, value.encode('latin-1', 'replace') )
			else:
				print >> cout, "  %s: %s" % ( key, value )
		print >> cout, "[end_log_entry]"

		result = cout.getvalue()

		if logfile or logdir :
			if logdir:
				# an absolute path for 'logdir' will override the standard ~/logs
				logfile = logfile or os.getenv("BM_CRITICAL_LOG", None)
				if not logfile :
					tt = time.localtime()
					logfile = os.path.join(
						os.environ["HOME"],
						"logs",
						logdir,
						"%04d%02d%02d.log" % ( tt[0], tt[1], tt[2] ),
					)

			try: os.makedirs(os.path.dirname(logfile))
			except: pass

			try:
				lout = open(logfile, "a")
				lout.write(result)
				sys.stderr.write(result)
			except:
				pass
		else:
			sys.stderr.write(result)

			if sys.stderr.isatty():
				sys.stderr.write("\n")

		sys.stderr.flush()

	finally:
		try: cout.close()
		except: pass

		if logfile:
			try: lout.close()
			except: pass

	return	result

Log.verbose = False
