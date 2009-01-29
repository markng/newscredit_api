#
#   bm_io.py
#
#   David Janes
#   2006.01.08
#
#	Stuff related to IO
#

import sys
import os
import random
import time
import fnmatch
import types
import gzip

def remove(path, **ad):
	os.remove(path)

IS_CYGWIN = hasattr(sys, "winver")

def findfile(filename, locale = None, paths = None, mode = "r"):
	"""Like readfile, except just returns the name (and no archives)"""

	if locale:
		locales = []
		if len(locale) == 5:
			locales.append("." + locale)
		if len(locale) >= 2:
			locales.append("." + locale[:2])
		locales.append("")
	else:
		locales = [ "" ]

	if paths and not os.path.isabs(filename):
		filenames = []
		for path in paths:
			for locale_extension in locales:
				filenames.append(os.path.join(path, filename + locale_extension))
	else:
		filenames = []
		for locale_extension in locales:
			filenames.append(filename + locale_extension)

	for filename in filenames:
		if os.path.isfile(filename):
			return	filename

	return	None

def readfile(filename, otherwise = None, locale = None, lf = None, paths = None, mode = "r", read_archives = False):
	"""Read a file and return it"""
	if locale:
		locales = []
		if len(locale) == 5:
			locales.append("." + locale)
		if len(locale) >= 2:
			locales.append("." + locale[:2])
		locales.append("")
	else:
		locales = [ "" ]

	if lf:
		lfs = []
		for locale in locales:
			lfs.append(".%s%s" % ( lf, locale, ))

		locales = lfs + locales

	if paths and not os.path.isabs(filename):
		filenames = []
		for path in paths:
			for locale_extension in locales:
				filenames.append(os.path.join(path, filename + locale_extension))
	else:
		filenames = []
		for locale_extension in locales:
			filenames.append(filename + locale_extension)

	from bm_log import Log

	for filename in filenames:
		filename = resolve_path(filename)
		try:
			try:
				from bm_log import Log
				fin = open(filename, mode)
				return	fin.read()
			finally:
				try: fin.close()
				except: pass
		except IOError, x:
			if not read_archives:
				continue

			if not x.errno == 20:
				continue

			#
			#	read through a tarfile
			#
			for ( tar_ext, tar_mode ) in [
			  ( ".tar.gz/", "r:gz" ),
			  ( ".tgz/", "r:gz" ),
			  ( ".tar/", "r" ),
			]:
				extx = filename.find(tar_ext)
				if extx == -1:
					continue

				path_fs, path_archive = filename[:extx + len(tar_ext) - 1], filename[extx + len(tar_ext):]

				try:
					import tarfile
					tar = tarfile.open(path_fs, tar_mode)

					try:
						fin = tar.extractfile(path_archive)
						if fin == None:
							fin = tar.extractfile("./" + path_archive)

						if fin:
							return	fin.read()
					finally:
						try: tar.close()
						except: pass

						try: fin.close()
						except: pass
				except:
					pass

		except Exception, x:
			pass


	if otherwise == None:
		raise	x
	else:
		return	otherwise

class AtomicWrite:
	"""Write to a file atomically.

	Use this as if you would 'open', excepting 'wb' is assumed for the mode.
	Partial files will not be written (or rather, saved to the given name)

	New feature: if data != None, it will be written and the file closed

	Parameters:
	timestamp - if non-None, the timestamp of the written file will be changed to this
	"""
	def __init__(self, filename, mode = "wb", makedirs = False, data = None, timestamp = None):
		if makedirs:
			dirpath = os.path.dirname(filename)
			if dirpath and not os.path.isdir(dirpath):
				os.makedirs(dirpath)

		self.__timestamp = timestamp
		self.__filename = filename
		self.__tmp_filename = "%s-%s-%s.tmp" % ( filename, str(random.random())[2:], time.time() )
		self.fout = open(self.__tmp_filename, mode)

		for a in dir(self.fout):
			if not hasattr(self, a):
				setattr(self, a, getattr(self.fout, a))

		if data != None:
			try:
				self.write(data)
				self.close()
			except:
				self.abort()
				raise

	def abort(self):
		try: self.fout.close()
		except: pass

		try: os.remove(self.__tmp_filename)
		except: pass

	def close(self):
		try: self.fout.close()
		except:
			self.abort()
			return

		os.rename(self.__tmp_filename, self.__filename)

		if self.__timestamp:
			os.utime(self.__filename, (( self.__timestamp, self.__timestamp, )))



def resolve_path(path, count = 0):
	if not IS_CYGWIN:
		return	path

	try:
		start = path

		if count == 0:
			path = os.path.normpath(path)

		if count > 8:
			return	path

		chopped = []
		while True:
			if os.path.exists(path):
				break

			lnk = path + '.lnk'
			if os.path.exists(path + '.lnk'):
				try:
					lnk_src = resolve_shortcut(lnk)
				except:
					lnk_src = lnk
					break

				# print "*0", count, lnk, lnk_src, chopped
				if chopped:
					path = resolve_path(lnk_src + "\\" + "\\".join(chopped), count + 1)
				else:
					path = resolve_path(lnk_src, count + 1)

				return	path

			head, tail = os.path.split(path)
			if head == path:
				break

			chopped.insert(0, tail)
			# print "*1", count, head, chopped
			path = head

		# print "*2", count, path, chopped
		if chopped:
			path += "\\" + "\\".join(chopped)

		# print "*3", count, path, chopped
		return	path
	finally:
		if count == 0 and False:
			print "**", start, path

def resolve_shortcut(filename):
	"""resolve_shortcut("Notepad.lnk") => "C:\WINDOWS\system32\notepad.exe"

	Returns the path refered to by a windows shortcut (.lnk) file.
	"""
	from win32com.shell import shell
	import pythoncom

	shell_link = pythoncom.CoCreateInstance(
		shell.CLSID_ShellLink, None,
		pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)

	persistant_file = shell_link.QueryInterface(pythoncom.IID_IPersistFile)

	persistant_file.Load(filename)

	shell_link.Resolve(0, 0)
	linked_to_file = shell_link.GetPath(shell.SLGP_UNCPRIORITY)[0]
	return linked_to_file

