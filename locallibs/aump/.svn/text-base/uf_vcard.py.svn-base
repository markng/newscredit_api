#
#	uf_vcard.py
#
#	David Janes
#	BlogMatrix
#	2006.11.27
#
#	Deal with 'vobject'
#

import sys
import os
import string
import pprint
import types
import re
import csv
import cStringIO as StringIO

from bm_log import Log

import uf_mfdict
import bm_locales
import bm_data_streets
import bm_text

#
#	Definitions

#
# grouping attributes are upper case
ADR = 'adr'
GEO = 'geo'
N = 'n'
ORG = 'org'
TEL = 'tel'

# meaning narrowers
Home = 'home'
Work = 'work'
Parcel = 'parcel'
Postal = 'postal'

# all others
FN = 'fn'

AdditionalName = 'additional-name'
FamilyName = 'family-name'
GivenName = 'given-name'
HonorificPrefix = 'honorific-prefix'
HonorificSuffix = 'honorific-suffix'
SortString = 'sort-string'
Nickname = 'nickname'

CountryName = 'country-name'
ExtendedAddress = 'extended-address'
Locality = 'locality'
PostOfficeBox = 'post-office-box'
PostalCode = 'postal-code'
Region = 'region'
StreetAddress = 'street-address'

Latitude = 'latitude'
Longitude = 'longitude'
TZ = 'tz'

Cell = 'mobile'
Mobile = 'mobile'
Fax = 'fax'
Msg = 'msg'
Pager = 'pager'
Voice = 'voice'

Bday = 'bday'
Category = 'category'
Class = 'class'
Email = 'email'
Key = 'key'
Label = 'label'
Mailer = 'mailer'
Note = 'note'
Photo = 'photo'
Rev = 'rev'
Role = 'role'
Sound = 'sound'
UID = 'uid'
URL = 'url'

# 3.5 ORGANIZATIONAL TYPES
Agent = 'agent'
Logo = 'logo'
OrganizationName = 'organization-name'
OrganizationUnit = 'organization-unit'
Title = 'title'
Type = 'type'

# these group like things together
card_structures = [
	ADR,
	N,
	ORG,
	GEO,
	TEL,
]

# ways of grouping information
card_groups = [
	"",
	Home,
	Work,
	Postal,
	Parcel,
]

#
#	Importing functions
#
try:
	import vobject

	def import_vcard(vin):
		"""Convert a _single_ vcard (text) to a mfdict. 

		Parameters:
		in - a string or a file object
		"""

		vcard = vobject.readOne(vin)
		mfd = uf_mfdict.mfdict()

		for child in vcard.getChildren():
			if type(child.value) not in types.StringTypes:
				child.value = unicode(child.value)

			if child.name == "N":
				d = dict(zip(vobject.vcard.NAME_ORDER, vobject.vcard.splitFields(child.value)))
			elif child.name == "ADR":
				d = dict(zip(vobject.vcard.ADDRESS_ORDER, vobject.vcard.splitFields(child.value)))
			else:
				d = { "" : child.value }

			ctype = child.params.get("TYPE", [])

			for key, value in d.iteritems():
				keys = filter(lambda s: s, [ child.name.lower(), key, ] + ctype)

				if type(value) == types.ListType:
					value = " ".join(value)

				value = clean_space(value)

				mfd.add(keys, value)

		return	mfd
except ImportError:
	pass

## csv scrubbing
thunderbird_headers = [
	'name-first', 'name-last', 'name-display', 'name-nickname', 'email', 'email-2', 
	'phone-work', 'phone-home', 'phone-fax', 'phone-pager', 'phone-mobile', 
	'home-adr', 'home-adr-2', 'home-city', 'home-prov', 'home-zip', 'home-country', 
	'work-adr', 'work-adr-2', 'work-city', 'work-prov', 'work-zip', 'work-country', 'work-title', 'work-department', 'work-org', 
	'work-url', 'home-url', '', '', '', '', '', '', '', '', ''
]

fieldd = {
	## google fields
	'name' : 'fn',
	'e-mail address' : 'email',
	'notes' : '',
	'e-mail 2' : 'email',
	'e-mail 3' : 'email',
	'mobile phone' : 'mobile',
	'pager' : 'page',
	'company' : 'org.organization-name',
	'job title' : 'title',
	'home phone' : 'home.voice',
	'home phone 2' : 'home.voice',
	'home fax' : 'home.fax',
	'home address' : 'home.location',
	'business phone' : 'work.voice',
	'business phone 2' : 'work.voice',
	'business fax' : 'work.fax',
	'business address' : 'work.location',
	'other phone' : 'voice',
	'other fax' : 'fax',
	'other address' : 'location',

	## google 2
	'name' : 'fn',
	'e-mail' : 'email',
	'notes' : '',
	'section 1 - description' : '',
	'section 1 - email' : 'email',
	'section 1 - im' : '',
	'section 1 - phone' : 'home.voice',
	'section 1 - mobile' : 'home.mobile',
	'section 1 - pager' : 'home.pager',
	'section 1 - fax' : 'home.fax',
	'section 1 - company' : 'org.organization-name',
	'section 1 - title' : 'title',
	'section 1 - other' : '',
	'section 1 - address' : 'home.location',
	'section 2 - description' : '',
	'section 2 - email' : 'work.email',
	'section 2 - im' : '',
	'section 2 - phone' : 'work.voice',
	'section 2 - mobile' : 'work.cell',
	'section 2 - pager' : 'work.pager',
	'section 2 - fax' : 'work.fax',
	'section 2 - company' : 'org.organization-name',
	'section 2 - title' : 'title',
	'section 2 - other' : '',
	'section 2 - address' : 'work.location',

	## IE fields
	'first name' : 'n.given-name',
	'last name' : 'n.family-name',
	'middle name' : 'n.additional-name',
	'name' : 'fn',
	'nickname' : 'nickname',
	'e-mail address' : 'email',
	'home street' : 'home.street-address',
	'home city' : 'home.locality',
	'home postal code' : 'home.postal-code',
	'home state' : 'home.region',
	'home country/region' : 'home.country-name',

	'home phone' : 'home.voice',
	'business street' : 'work.street-address',
	'business city' : 'work.locality',
	'business postal code' : 'work.postal-code',
	'business state' : 'work.region',
	'business country/region' : 'work.country-name',
	'business phone' : 'work.voice',
	'company' : 'org.organization-name',
	'job title' : 'title',

	## Thunderbird
	'name-first' : 'n.first-name',
	'name-last' : 'n.last-name',
	'name-display' : 'fn',
	'name-nickname' : 'nickname',
	'email' : 'email',
	'email-2' : 'email',
	'phone-work' : 'work.voice',
	'phone-home' : 'home.voice',
	'phone-fax' : 'fax',
	'phone-pager' : 'pager',
	'phone-mobile' : 'mobile',
	'home-adr' : 'home.street-address',
	'home-adr-2' : 'home.',
	'home-city' : 'home.locality',
	'home-prov' : 'home.region',
	'home-zip' : 'home.postal-code',
	'home-country' : 'home.country-name',
	'work-adr' : 'work.street-address',
	'work-adr-2' : 'work.extended-address',
	'work-city' : 'work.locality',
	'work-prov' : 'work.region',
	'work-zip' : 'work.postal-code',
	'work-country' : 'work.country-name',
	'work-title' : 'title',
	'work-department' : 'org.organization-unit',
	'work-org' : 'org.organization-name',
	'work-url' : 'work.url',
	'home-url' : 'url',
}

def import_csv(str):
	"""Import vcards from a CSV export file
	
	Note:
	- this does not do any scrubbing
	"""

	result = []

	din = StringIO.StringIO(str)
	try:
		csv_reader = csv.reader(din)

		mta = ""

		headers = None
		for line in csv_reader:
			# Log(line = line)
			if headers == None:
				headers = map(lambda k: fieldd.get(k.lower(), ''), line)

				## no (or few) matches in header is indicative that we're looking at firefox
				if len(filter(lambda k: k, headers)) <= 5 and headers[0] == '':
					headers = map(lambda k: fieldd.get(k.lower(), ''), thunderbird_headers)
					mta = "thunderbird"

				# Log("HEADERS", headers_out = headers, line = line)
			else:
				line = map(bm_text.tounicode, line)

				mfd = uf_mfdict.mfdict()
				for key, item in zip(headers, line):
					if key and item:
						mfd.add(key, item)

				## a common juxtiposition
				for prefix in [ "home.", "work.", "" ]:
					a_key = prefix + 'street-address'
					a_value = mfd.get(a_key)
					if not a_value:	
						continue

					b_key = prefix + 'extended-address'
					b_value = mfd.get(b_key)
					if not b_value:	
						continue

					mfd[a_key] = b_value
					mfd[b_value] = a_value

				result.append(mfd)
	finally:
		try: din.close()
		except: pass

	return	result

#
#	Scrubbing functions 
#
fn_not_ok_re = "[^-a-z0-9]"
fn_not_ok_rex = re.compile(fn_not_ok_re, re.I|re.MULTILINE|re.DOTALL)

fn_comment_re = "\([^)]*\)"
fn_comment_rex = re.compile(fn_comment_re, re.I|re.MULTILINE|re.DOTALL)

space_res = [
	(
		" +", " ",
	),
	(
		" *\r\n *", "\n",
	)
]
space_rexs = map(lambda (a, b): ( re.compile(a, re.I|re.MULTILINE|re.DOTALL), b ), space_res)

def clean_space(value):
	if type(value) not in types.StringTypes:
		return	value

	for rex, replace in space_rexs:
		value = rex.sub(replace, value)

	return	value.strip()

def scrub_space(mfd):
	for key, value in list(mfd.iteritems()):
		nvalue = clean_space(value)
		if nvalue != value:	
			mfd[key] = nvalue

def scrub_fn(mfd, otherwise_fn = 'No Name'):
	"""Scrub the FN of a contact"""

	fn = mfd.find(FN, '')
	if not fn:
		fn = \
			mfd.find(ORG, '') or \
			mfd.find(OrganizationName , '') or \
			mfd.find(Email, '') or \
			''

	atx = fn.find('@')
	if atx > -1:
		fn = fn[:atx]

		fn = fn_not_ok_rex.sub(" ", fn)
		fn = string.capwords(fn)
	else:
		if fn[:1] in [ "'", '"', ] and fn[:1] == fn[-1:]:
			fn = fn[1:-1]

		fn = fn_comment_rex.sub(" ", fn)
		fn = " ".join(map(lambda s: s[:1].upper() + s[1:], fn.split()))

	if not fn:
		fn = otherwise_fn or ""

	mfd[FN] = fn

def scrub_email(mfd):
	for key, value in mfd.finditems(Email):
		if value.startswith("mailto:"):
			mfd[key] = value[7:]


extended_re = "[\n,]"
extended_rex = re.compile(extended_re, re.I|re.MULTILINE|re.DOTALL)

def scrub_address(mfd):
	"""Try to fill in missing fields in addresses"""
	adr_keys = [ ExtendedAddress, StreetAddress, Locality, Region, CountryName, PostalCode, Email, ]

	for card_group in card_groups:
		adrd = uf_mfdict.mfdict()
		keyd = {}

		for adr_key in adr_keys:
			if card_group == "":
				in_key = adr_key
				out_key, out_value = mfd.finditem(in_key, exclude_keys = card_groups)
			else:
				in_key = "%s.%s" % ( card_group, adr_key )
				out_key, out_value = mfd.finditem(in_key)

			adrd[out_key or in_key] = out_value or ""
			keyd[adr_key] = out_key or in_key

		if not filter(lambda s: s, adrd.values()):
			continue

		pprint.pprint((card_group, adrd), sys.stderr)

		#
		#	Fix up
		#
		parts = extended_rex.split(adrd[keyd[StreetAddress]])
		parts = filter(lambda s: s, parts)
		if len(parts) > 1:
			parts = map(lambda s: s.strip(), parts)

			adrd[keyd[StreetAddress]] = parts[-1]

			parts = parts[:-1]

			extended = adrd[keyd[ExtendedAddress]] 
			if extended:
				parts.append(extended)

			adrd[keyd[ExtendedAddress]] = ", ".join(parts)

		#
		#	By telephone #
		#
		tel = mfd.find(Voice) or mfd.find(Cell) or mfd.find(TEL) 
		if tel and ( not adrd[keyd[Region]] or not adrd[keyd[CountryName]] ) and tel:
			result = LookupPhone(phone = tel)

			if not adrd[keyd[Locality]] and result.get(Locality):
				adrd[keyd[Locality]] = result[Locality]
			if not adrd[keyd[Region]] and result.get(Region):
				adrd[keyd[Region]] = result[Region]
			if not adrd[keyd[CountryName]] and result.get(CountryName):
				adrd[keyd[CountryName]] = result[CountryName]

		#
		#	By postal code
		#
		if ( not adrd[keyd[Region]] or not adrd[keyd[CountryName]] ) and adrd.find(PostalCode):
			result = LookupPostalCode(adrd.find(PostalCode))

			for k in [ PostalCode, CountryName, Region, Locality ]:
				value = result.get(k)
				if value:
					adrd[keyd[k]] = value

		#
		#	By name of region
		#
		result = LookupRegionCountry(region = adrd[keyd[Region]], country = adrd[keyd[CountryName]])
		adrd[keyd[Region]] = result[Region]
		adrd[keyd[CountryName]] = result[CountryName]

		#
		#	Scrub street
		#
		result = LookupStreet(street = adrd[keyd[StreetAddress]], region = adrd[keyd[Region]], country = adrd[keyd[CountryName]])
		adrd[keyd[StreetAddress]] = result[StreetAddress]

		for key, value in adrd.iteritems():
			if value:
				mfd[key] = value

#
#	Convert state and province names to ( state-name, country-name )
#
region_normalize = {
	"nf" : ( "Newfoundland and Labrador", "Canada", ),
	"newfoundland" : ( "Newfoundland and Labrador", "Canada", ),
	"labrador" : ( "Newfoundland and Labrador", "Canada", ),
}
for province, name in bm_locales.ca_province_map.iteritems():
	region_normalize[province.lower()] = ( name, "Canada", )
	region_normalize[name.lower()] = ( name, "Canada", )

for state, name in bm_locales.us_state_map.iteritems():
	region_normalize[state.lower()] = ( name, "United States", )
	region_normalize[name.lower()] = ( name, "United States", )

pattern_res = [
	"^(?P<area_code>\d{3}) ",
	"^1 (?P<area_code>\d{3}) ",
	"^[+]1 (?P<area_code>\d{3}) ",
	"^[+](?P<country_code>\d{1,3})",
]

def LookupPhone(phone):
	phone = re.sub("[^+\d]", " ", phone)
	phone = re.sub("\s+", " ", phone)

	country_code = None
	area_code = None

	for pattern in pattern_res:
		match = re.search(pattern, phone)
		if match:
			try: area_code = match.group("area_code")
			except: pass

			try: country_code = match.group("country_code")
			except: pass

			break

	if area_code:
		area_code_map = bm_locales.area_code(area_code)
		if area_code_map:
			country = area_code_map.get("country")
			country = bm_locales.country_to_name(country)

			state = area_code_map.get("state")
			state, x = region_normalize.get(state.lower(), ( state, country ))

			return	{
				Region : state,
				CountryName : country,
				Locality : area_code_map.get("locality"),
			}
	elif country_code:
		for x in xrange(1, len(country_code) + 1):
			country_code_map = bm_locales.itu_calling_code(country_code[:x])
			if country_code_map:
				country = country_code_map.get("country")
				country = bm_locales.country_to_name(country)

				return	{
					CountryName : country,
				}

	return	{}

def LookupRegionCountry(region, country):
	"""This will convert 'region' and 'country' into the best (English language) strings ever

	Keyword arguments:
	region -- the name of a region (state or province) (or null)
	country -- the name of a country (or null)
	"""
	if country and len(country) == 2:
		country = bm_locales.country_to_name(country)

	if country:
		if country == "U.S.A.": country = "United States"
		elif country == "USA.": country = "United States"
		elif country == "USA": country = "United States"

	if country in [ "Canada", "United States" ] and region:
		region, x = region_normalize.get(region.lower(), ( region, country ))

	if not country and region:
		region, country = region_normalize.get(region.lower(), ( region, country ))

	return	{
		Region : region or "", 
		CountryName : country or "",
	}

canada_re = "^([abceghjlmnprstvyx][0-9][a-z])\s*([0-9][a-z][0-9])$"
canada_rex = re.compile(canada_re, re.I)

def LookupPostalCode(postal_code):
	d = {}

	postal_code = postal_code.strip()
	if not postal_code:
		return	{}

	canada_match = canada_rex.match(postal_code)
	if canada_match:
		d = {
			PostalCode : "%s %s" % ( canada_match.group(1).upper(), canada_match.group(2).upper(), ),
			CountryName : "Canada",
		}

		first = canada_match.group(1).upper()[0]

		if first == 'A': d[Region] = 'Newfoundland and Labrador'
		elif first == 'B': d[Region] = 'Nova Scotia'
		elif first == 'C': d[Region] = 'Prince Edward Island'
		elif first == 'E': d[Region] = 'New Brunswick'
		elif first in [ 'G', 'H', 'J' ]: d[Region] = 'Quebec'
		elif first == 'M':
			d[Region] = 'Ontario'
			d[Locality] = 'Toronto'
		elif first in [ 'L', 'N', 'P', ]: d[Region] = 'Ontario'
		elif first == 'R': d[Region] = 'Manitoba'
		elif first == 'S': d[Region] = 'Saskatchewan'
		elif first == 'T': d[Region] = 'Alberta'
		elif first == 'V': d[Region] = 'British Columbiz'
		elif first == 'Y': d[Region] = 'Yukon'

	return	d

direction_map = {
	"e" : "East",
	"w" : "West",
	"n" : "North",
	"s" : "South",
	"e." : "East",
	"w." : "West",
	"n." : "North",
	"s." : "South",
}

def LookupStreet(street, region, country):
	"""Convert 'rd.' to 'Road', etc.  'LookupRegionCountry' should be called first.

	Keyword arguments:
	street -- the name of a street (19 Glasgow Pl.)
	region -- the name of a region (state or province) (or null)
	country -- the name of a country (or null)
	"""
	street_parts = street.split()
	if street_parts:
		direction = direction_map.get(street_parts[-1].lower())
		if direction:
			street_parts[-1] = direction

		for spi in xrange(len(street_parts)):
			part = street_parts[spi].rstrip(".").lower()

			translation = bm_data_streets.street_map.get(part)
			if translation:
				street_parts[spi] = translation

		street = " ".join(street_parts)

	return {
		StreetAddress : street,
	}

def scrub(mfd):
	"""Scrub everything we can in a contact"""
	scrub_email(mfd)
	scrub_fn(mfd)
	scrub_address(mfd)
	scrub_space(mfd)

def underscore2dash(d):
	"""Convert a dictionary using '_' to one using '-'"""
	rd = uf_mfdict.mfdict()

	for key, value in d.iteritems():
		rd[key.replace("_", "-")] = value

	return	rd

