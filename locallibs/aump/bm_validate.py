#
#   bm_validate.py
#
#   David Janes
#   2005.04.13
#

import re
import types
import os
import urlparse

try:
	import bm_config
except ImportError:
	class Config: 
		def get_msg(self, key, *av, **ad):
			return	key

	bm_config = Config()

email_re = """
	^
	[0-9a-z][-+._0-9a-z]*
	@
	[0-9a-z][-._0-9a-z]*
	[.]
	 (  com                               #     TLD
	 |  edu                               #
	 |  biz                               #
	 |  gov                               #
	 |  in(?:t|fo)                        #     .int or .info
	 |  mil                               #
	 |  net                               #
	 |  org                               #
	 |  museum                            #
	 |  aero                              #
	 |  coop                              #
	 |  name                              #
	 |  pro                               #
	 |  [a-z][a-z]                        #     two-letter country codes
	 )                                    #
$
"""
email_rex = re.compile(email_re, re.I|re.VERBOSE)

def validate_email(email, lang = 'en'):
	assert(type(email) in types.StringTypes)

	if email_rex.match(email) == None:
		return bm_config.get_msg("email_invalid", "Invalid e-mail address", lang = lang)

emails_re = "^([0-9a-zA-Z]([-.\w]*[0-9a-zA-Z])*@([0-9a-zA-Z][-\w]*[0-9a-zA-Z]*\.)+[a-zA-Z]{1,9})([\s]*[,]?[\s]*(([0-9a-zA-Z]([-.\w]*[0-9a-zA-Z])*@([0-9a-zA-Z][-\w]*[0-9a-zA-Z]*\.)+[a-zA-Z]{1,9})))*"
emails_rex = re.compile(emails_re, re.I)

def validate_emails(email, lang = 'en'):
	""" Validate a list of emails, either separated by spaces or a comma """
	assert(type(email) in types.StringTypes)

	if emails_rex.match(email) == None:
		return bm_config.get_msg("email_invalid", "Invalid e-mail address", lang = lang)

# taken from textile
uri_re = r'''^
			 (?=[a-zA-Z0-9./#])                         # Must start correctly
			 (?:                                        # Match the leading part (proto://hostname, or just hostname)
				 (?:ftp|https?|telnet|nntp)             #     protocol
				 ://                                    #     ://
				 (?:                                    #     Optional 'username:password@'
					 \w+                                #         username
					 (?::\w+)?                          #         optional :password
					 @                                  #         @
				 )?                                     #
				 [-\w]+(?:\.\w[-\w]*)+                  #     hostname (sub.example.com)
			 |                                          #
				 (?:mailto:)?                           #     Optional mailto:
				 [-\+\w]+                               #     username
				 \@                                     #     at
				 [-\w]+(?:\.\w[-\w]*)+                  #     hostname
			 |                                          #
				 (?:[a-z0-9](?:[-a-z0-9]*[a-z0-9])?\.)+ #     domain without protocol
				 (?:com\b                               #     TLD
				 |  edu\b                               #
				 |  biz\b                               #
				 |  gov\b                               #
				 |  in(?:t|fo)\b                        #     .int or .info
				 |  mil\b                               #
				 |  net\b                               #
				 |  org\b                               #
				 |  museum\b                            #
				 |  aero\b                              #
				 |  coop\b                              #
				 |  name\b                              #
				 |  pro\b                               #
				 |  [a-z][a-z]\b                        #     two-letter country codes
				 )                                      #
			 )?                                         #
			 (?::\d+)?                                  # Optional port number
			 (?:                                        # Rest of the URL, optional
				 /?                                     #     Start with '/'
				 [^.!,?;:"'<>()\[\]{}\s\x7F-\xFF]*      #     Can't start with these
				 (?:                                    #
					 [.!,?;:]+                          #     One or more of these
					 [^.!,?;:"'<>()\[\]{}\s\x7F-\xFF]+  #     Can't finish with these
					 #'"                                #     # or ' or "
				 )*                                     #
			 )?                                         #
			 $
		  '''
uri_rex = re.compile(uri_re, re.I|re.VERBOSE)

host_re = """
	^
	[0-9a-z][-._0-9a-z]*
	[.]
	 (  com                               #     TLD
	 |  edu                               #
	 |  biz                               #
	 |  gov                               #
	 |  in(?:t|fo)                        #     .int or .info
	 |  mil                               #
	 |  net                               #
	 |  org                               #
	 |  museum                            #
	 |  aero                              #
	 |  coop                              #
	 |  name                              #
	 |  pro                               #
	 |  [a-z][a-z]                        #     two-letter country codes
	 )                                    #
	 (:[\d]+)?							  #	port
$
"""
host_rex = re.compile(host_re, re.I|re.VERBOSE)

def validate_uri(uri, schemes = None, lang = 'en'):
	assert(type(uri) in types.StringTypes)

	if not uri_rex.match(uri):
		return	bm_config.get_msg('invalid_uri')

	urit = urlparse.urlparse(uri)

	if schemes:
		colonx = uri.find(':')
		if colonx == -1:
			return bm_config.get_msg('uri_no_schema')

		if urit[0] not in schemes:
			return	bm_config.get_msg('invalid_uri_schema')

	#
	#	2007-08-28 dpj
	#	*new* make sure we have a proper domain name
	#
	if urit[0] in [ "http", "https", "ftp" ]:
		if not host_rex.match(urit[1]):
			return	bm_config.get_msg("invalid_uri_host")

	return	None
