#
#   bm_locales.py
#
#   David Janes
#   2005.04.19
#
#	Country codes and languages
#

#
#	Known Locales (map string->unicode)
#	- this will map the locale string into the language name.
#
language_map = {
	"aa" : u"Afar",
	"ab" : u"Abkhazian",
	"af" : u"Afrikaans",
	"am" : u"Amharic",
	"ar" : u"Arabic",
	"as" : u"Assamese",
	"ay" : u"Aymara",
	"az" : u"Azerbaijani",
	"ba" : u"Bashkir",
	"be" : u"Byelorussian",
	"bg" : u"Bulgarian",
	"bh" : u"Bihari",
	"bi" : u"Bislama",
	"bn" : u"Bengali",
	"bo" : u"Tibetan",
	"br" : u"Breton",
	"ca" : u"Catalan",
	"co" : u"Corsican",
	"cs" : u"Czech",
	"cy" : u"Welsh",
	"da" : u"Danish",
	"de" : u"German",
	"dz" : u"Bhutani",
	"el" : u"Greek",
	"en" : u"English",
	"eo" : u"Esperanto",
	"es" : u"Spanish",
	"et" : u"Estonian",
	"eu" : u"Basque",
	"fa" : u"Persian",
	"fi" : u"Finnish",
	"fj" : u"Fiji",
	"fo" : u"Faeroese",
	"fr" : u"French",
	"fy" : u"Frisian",
	"ga" : u"Irish",
	"gd" : u"Gaelic",
	"gl" : u"Galician",
	"gn" : u"Guarani",
	"gu" : u"Gujarati",
	"ha" : u"Hausa",
	"he" : u"Hebrew",
	"hi" : u"Hindi",
	"hr" : u"Croatian",
	"hu" : u"Hungarian",
	"hy" : u"Armenian",
	"ia" : u"Interlingua",
	"ie" : u"Interlingue",
	"ik" : u"Inupiak",
	"in" : u"Indonesian",
	"is" : u"Icelandic",
	"it" : u"Italian",
	"iw" : u"Hebrew",
	"ja" : u"Japanese",
	"ji" : u"Yiddish",
	"jw" : u"Javanese",
	"ka" : u"Georgian",
	"kk" : u"Kazakh",
	"kl" : u"Greenlandic",
	"km" : u"Cambodian",
	"kn" : u"Kannada",
	"ko" : u"Korean",
	"ks" : u"Kashmiri",
	"ku" : u"Kurdish",
	"ky" : u"Kirghiz",
	"la" : u"Latin",
	"ln" : u"Lingala",
	"lo" : u"Laothian",
	"lt" : u"Lithuanian",
	"lv" : u"Latvian",
	"mg" : u"Malagasy",
	"mi" : u"Maori",
	"mk" : u"Macedonian",
	"ml" : u"Malayalam",
	"mn" : u"Mongolian",
	"mo" : u"Moldavian",
	"mr" : u"Marathi",
	"ms" : u"Malay",
	"mt" : u"Maltese",
	"my" : u"Burmese",
	"na" : u"Nauru",
	"ne" : u"Nepali",
	"nl" : u"Dutch",
	"no" : u"Norwegian",
	"oc" : u"Occitan",
	"om" : u"Oromo",
	"or" : u"Oriya",
	"pa" : u"Punjabi",
	"pl" : u"Polish",
	"ps" : u"Pashto",
	"pt" : u"Portuguese",
	"qu" : u"Quechua",
	"rm" : u"Rhaeto-Romance",
	"rn" : u"Kirundi",
	"ro" : u"Romanian",
	"ru" : u"Russian",
	"rw" : u"Kinyarwanda",
	"sa" : u"Sanskrit",
	"sd" : u"Sindhi",
	"sg" : u"Sangro",
	"sh" : u"Serbo-Croatian",
	"si" : u"Singhalese",
	"sk" : u"Slovak",
	"sl" : u"Slovenian",
	"sm" : u"Samoan",
	"sn" : u"Shona",
	"so" : u"Somali",
	"sq" : u"Albanian",
	"sr" : u"Serbian",
	"ss" : u"Siswati",
	"st" : u"Sesotho",
	"su" : u"Sudanese",
	"sv" : u"Swedish",
	"sw" : u"Swahili",
	"ta" : u"Tamil",
	"te" : u"Tegulu",
	"tg" : u"Tajik",
	"th" : u"Thai",
	"ti" : u"Tigrinya",
	"tk" : u"Turkmen",
	"tl" : u"Tagalog",
	"tn" : u"Setswana",
	"to" : u"Tonga",
	"tr" : u"Turkish",
	"ts" : u"Tsonga",
	"tt" : u"Tatar",
	"tw" : u"Twi",
	"uk" : u"Ukrainian",
	"ur" : u"Urdu",
	"uz" : u"Uzbek",
	"vi" : u"Vietnamese",
	"vo" : u"Volapuk",
	"wo" : u"Wolof",
	"xh" : u"Xhosa",
	"yo" : u"Yoruba",
	"zh" : u"Chinese",
	"zu" : u"Zulu",
}

def language_to_name(code):
	code = code.lower()
	return	language_map.get(code, code)

language_name_map = None

def language_to_code(name, otherwise = None):
	global language_name_map

	name = name.lower()

	if language_map.get(name):
		return	name
	
	if language_name_map == None:
		language_name_map = {}
		for code, value in language_map.iteritems():
			language_name_map[value.lower()] = code

	return	language_name_map.get(name, otherwise)

country_map = {
	"AD" : u"Andorra, Principality of",
	"AE" : u"United Arab Emirates",
	"AF" : u"Afghanistan, Islamic State of",
	"AG" : u"Antigua and Barbuda",
	"AI" : u"Anguilla",
	"AL" : u"Albania",
	"AM" : u"Armenia",
	"AN" : u"Netherlands Antilles",
	"AO" : u"Angola",
	"AQ" : u"Antarctica",
	"AR" : u"Argentina",
	"AS" : u"American Samoa",
	"AT" : u"Austria",
	"AU" : u"Australia",
	"AW" : u"Aruba",
	"AZ" : u"Azerbaidjan",
	"BA" : u"Bosnia-Herzegovina",
	"BB" : u"Barbados",
	"BD" : u"Bangladesh",
	"BE" : u"Belgium",
	"BF" : u"Burkina Faso",
	"BG" : u"Bulgaria",
	"BH" : u"Bahrain",
	"BI" : u"Burundi",
	"BJ" : u"Benin",
	"BM" : u"Bermuda",
	"BN" : u"Brunei Darussalam",
	"BO" : u"Bolivia",
	"BR" : u"Brazil",
	"BS" : u"Bahamas",
	"BT" : u"Bhutan",
	"BV" : u"Bouvet Island",
	"BW" : u"Botswana",
	"BY" : u"Belarus",
	"BZ" : u"Belize",
	"CA" : u"Canada",
	"CC" : u"Cocos (Keeling) Islands",
	"CF" : u"Central African Republic",
	"CD" : u"Congo, The Democratic Republic of the",
	"CG" : u"Congo",
	"CH" : u"Switzerland",
	"CI" : u"Ivory Coast (Cote D'Ivoire)",
	"CK" : u"Cook Islands",
	"CL" : u"Chile",
	"CM" : u"Cameroon",
	"CN" : u"China",
	"CO" : u"Colombia",
	"CR" : u"Costa Rica",
	"CS" : u"Former Czechoslovakia",
	"CU" : u"Cuba",
	"CV" : u"Cape Verde",
	"CX" : u"Christmas Island",
	"CY" : u"Cyprus",
	"CZ" : u"Czech Republic",
	"DE" : u"Germany",
	"DJ" : u"Djibouti",
	"DK" : u"Denmark",
	"DM" : u"Dominica",
	"DO" : u"Dominican Republic",
	"DZ" : u"Algeria",
	"EC" : u"Ecuador",
	"EE" : u"Estonia",
	"EG" : u"Egypt",
	"EH" : u"Western Sahara",
	"ER" : u"Eritrea",
	"ES" : u"Spain",
	"ET" : u"Ethiopia",
	"FI" : u"Finland",
	"FJ" : u"Fiji",
	"FK" : u"Falkland Islands",
	"FM" : u"Micronesia",
	"FO" : u"Faroe Islands",
	"FR" : u"France",
	"FX" : u"France (European Territory)",
	"GA" : u"Gabon",
	"GB" : u"Great Britain",
	"GD" : u"Grenada",
	"GE" : u"Georgia",
	"GF" : u"French Guyana",
	"GH" : u"Ghana",
	"GI" : u"Gibraltar",
	"GL" : u"Greenland",
	"GM" : u"Gambia",
	"GN" : u"Guinea",
	"GP" : u"Guadeloupe (French)",
	"GQ" : u"Equatorial Guinea",
	"GR" : u"Greece",
	"GS" : u"S. Georgia & S. Sandwich Isls.",
	"GT" : u"Guatemala",
	"GU" : u"Guam (USA)",
	"GW" : u"Guinea Bissau",
	"GY" : u"Guyana",
	"HK" : u"Hong Kong",
	"HM" : u"Heard and McDonald Islands",
	"HN" : u"Honduras",
	"HR" : u"Croatia",
	"HT" : u"Haiti",
	"HU" : u"Hungary",
	"ID" : u"Indonesia",
	"IE" : u"Ireland",
	"IL" : u"Israel",
	"IN" : u"India",
	"IO" : u"British Indian Ocean Territory",
	"IQ" : u"Iraq",
	"IR" : u"Iran",
	"IS" : u"Iceland",
	"IT" : u"Italy",
	"JM" : u"Jamaica",
	"JO" : u"Jordan",
	"JP" : u"Japan",
	"KE" : u"Kenya",
	"KG" : u"Kyrgyz Republic (Kyrgyzstan)",
	"KH" : u"Cambodia, Kingdom of",
	"KI" : u"Kiribati",
	"KM" : u"Comoros",
	"KN" : u"Saint Kitts & Nevis Anguilla",
	"KP" : u"North Korea",
	"KR" : u"South Korea",
	"KW" : u"Kuwait",
	"KY" : u"Cayman Islands",
	"KZ" : u"Kazakhstan",
	"LA" : u"Laos",
	"LB" : u"Lebanon",
	"LC" : u"Saint Lucia",
	"LI" : u"Liechtenstein",
	"LK" : u"Sri Lanka",
	"LR" : u"Liberia",
	"LS" : u"Lesotho",
	"LT" : u"Lithuania",
	"LU" : u"Luxembourg",
	"LV" : u"Latvia",
	"LY" : u"Libya",
	"MA" : u"Morocco",
	"MC" : u"Monaco",
	"MD" : u"Moldavia",
	"MG" : u"Madagascar",
	"MH" : u"Marshall Islands",
	"MK" : u"Macedonia",
	"ML" : u"Mali",
	"MM" : u"Myanmar",
	"MN" : u"Mongolia",
	"MO" : u"Macau",
	"MP" : u"Northern Mariana Islands",
	"MQ" : u"Martinique (French)",
	"MR" : u"Mauritania",
	"MS" : u"Montserrat",
	"MT" : u"Malta",
	"MU" : u"Mauritius",
	"MV" : u"Maldives",
	"MW" : u"Malawi",
	"MX" : u"Mexico",
	"MY" : u"Malaysia",
	"MZ" : u"Mozambique",
	"NA" : u"Namibia",
	"NC" : u"New Caledonia (French)",
	"NE" : u"Niger",
	"NF" : u"Norfolk Island",
	"NG" : u"Nigeria",
	"NI" : u"Nicaragua",
	"NL" : u"Netherlands",
	"NO" : u"Norway",
	"NP" : u"Nepal",
	"NR" : u"Nauru",
	"NT" : u"Neutral Zone",
	"NU" : u"Niue",
	"NZ" : u"New Zealand",
	"OM" : u"Oman",
	"PA" : u"Panama",
	"PE" : u"Peru",
	"PF" : u"Polynesia (French)",
	"PG" : u"Papua New Guinea",
	"PH" : u"Philippines",
	"PK" : u"Pakistan",
	"PL" : u"Poland",
	"PM" : u"Saint Pierre and Miquelon",
	"PN" : u"Pitcairn Island",
	"PR" : u"Puerto Rico",
	"PT" : u"Portugal",
	"PW" : u"Palau",
	"PY" : u"Paraguay",
	"QA" : u"Qatar",
	"RE" : u"Reunion (French)",
	"RO" : u"Romania",
	"RU" : u"Russian Federation",
	"RW" : u"Rwanda",
	"SA" : u"Saudi Arabia",
	"SB" : u"Solomon Islands",
	"SC" : u"Seychelles",
	"SD" : u"Sudan",
	"SE" : u"Sweden",
	"SG" : u"Singapore",
	"SH" : u"Saint Helena",
	"SI" : u"Slovenia",
	"SJ" : u"Svalbard and Jan Mayen Islands",
	"SK" : u"Slovak Republic",
	"SL" : u"Sierra Leone",
	"SM" : u"San Marino",
	"SN" : u"Senegal",
	"SO" : u"Somalia",
	"SR" : u"Suriname",
	"ST" : u"Saint Tome (Sao Tome) and Principe",
	"SU" : u"Former USSR",
	"SV" : u"El Salvador",
	"SY" : u"Syria",
	"SZ" : u"Swaziland",
	"TC" : u"Turks and Caicos Islands",
	"TD" : u"Chad",
	"TF" : u"French Southern Territories",
	"TG" : u"Togo",
	"TH" : u"Thailand",
	"TJ" : u"Tadjikistan",
	"TK" : u"Tokelau",
	"TM" : u"Turkmenistan",
	"TN" : u"Tunisia",
	"TO" : u"Tonga",
	"TP" : u"East Timor",
	"TR" : u"Turkey",
	"TT" : u"Trinidad and Tobago",
	"TV" : u"Tuvalu",
	"TW" : u"Taiwan",
	"TZ" : u"Tanzania",
	"UA" : u"Ukraine",
	"UG" : u"Uganda",
	"UK" : u"United Kingdom",
	"UM" : u"USA Minor Outlying Islands",
	"US" : u"United States",
	"UY" : u"Uruguay",
	"UZ" : u"Uzbekistan",
	"VA" : u"Holy See (Vatican City State)",
	"VC" : u"Saint Vincent & Grenadines",
	"VE" : u"Venezuela",
	"VG" : u"Virgin Islands (British)",
	"VI" : u"Virgin Islands (USA)",
	"VN" : u"Vietnam",
	"VU" : u"Vanuatu",
	"WF" : u"Wallis and Futuna Islands",
	"WS" : u"Samoa",
	"YE" : u"Yemen",
	"YT" : u"Mayotte",
	"YU" : u"Yugoslavia",
	"ZA" : u"South Africa",
	"ZM" : u"Zambia",
	"ZR" : u"Zaire",
	"ZW" : u"Zimbabwe",
}

country_name_map = None

def country_to_code(name, otherwise = None):
	global country_name_map

	name = name.upper()

	if country_map.get(name):
		return	name
	
	if country_name_map == None:
		country_name_map = {}
		for code, value in country_map.iteritems():
			country_name_map[value.upper()] = code

	return	country_name_map.get(name, otherwise)

def country_to_name(code):
	return	country_map.get(code.upper(), code)

#
#	States and Provinces
#

us_state_map = {
	'al' : 'Alabama',
	'ak' : 'Alaska',
	'az' : 'Arizona',
	'ar' : 'Arkansas',
	'ca' : 'California',
	'co' : 'Colorado',
	'ct' : 'Connecticut',
	'de' : 'Delaware',
	'dc' : 'DC',
	'fl' : 'Florida',
	'ga' : 'Georgia',
	'hi' : 'Hawaii',
	'id' : 'Idaho',
	'il' : 'Illinois',
	'in' : 'Indiana',
	'ia' : 'Iowa',
	'ks' : 'Kansas',
	'ky' : 'Kentucky',
	'la' : 'Louisiana',
	'me' : 'Maine',
	'md' : 'Maryland',
	'ma' : 'Massachusetts',
	'mi' : 'Michigan',
	'mn' : 'Minnesota',
	'ms' : 'Mississippi',
	'mo' : 'Missouri',
	'mt' : 'Montana',
	'ne' : 'Nebraska',
	'nv' : 'Nevada',
	'nh' : 'New Hampshire',
	'nj' : 'New Jersey',
	'nm' : 'New Mexico',
	'ny' : 'New York',
	'nc' : 'North Carolina',
	'nd' : 'North Dakota',
	'oh' : 'Ohio',
	'ok' : 'Oklahoma',
	'or' : 'Oregon',
	'pa' : 'Pennsylvania',
	'ri' : 'Rhode Island',
	'sc' : 'South Carolina',
	'sd' : 'South Dakota',
	'tn' : 'Tennessee',
	'tx' : 'Texas',
	'ut' : 'Utah',
	'vt' : 'Vermont',
	'va' : 'Virginia',
	'wa' : 'Washington',
	'wv' : 'West Virginia',
	'wi' : 'Wisconsin',
	'wy' : 'Wyoming',
}

us_state_name_map = None

def state_code_to_name(code, otherwise = None):
	return	us_state_map.get(code.lower(), otherwise)
	
def state_to_code(name, otherwise = None):
	global us_state_name_map

	name = name.lower()

	if us_state_map.get(name):
		return	name
	
	if us_state_name_map == None:
		us_state_name_map = {}
		for code, value in us_state_map.iteritems():
			us_state_name_map[value.lower()] = code

	return	us_state_name_map.get(name, otherwise)

ca_province_map = {
	'ab' : 'Alberta',
	'bc' : 'British Columbia',
	'mb' : 'Manitoba',
	'nb' : 'New Brunswick',
	'nl' : 'Newfoundland and Labrador',
	'nt' : 'Northwest Territories',
	'ns' : 'Nova Scotia',
	'nu' : 'Nunavut',
	'on' : 'Ontario',
	'pe' : 'Prince Edward Island',
	'qc' : 'Quebec',
	'sk' : 'Saskatchewan',
	'yt' : 'Yukon',
}

ca_province_name_map = None

def province_code_to_name(code, otherwise = None):
	if code == "nf": code = "nl"
	return	ca_province_map.get(code.lower(), otherwise)
	
def province_to_code(name, otherwise = None):
	global ca_province_name_map

	name = name.lower()

	if ca_province_map.get(name):
		return	name
	
	if ca_province_name_map == None:
		ca_province_name_map = {}
		for code, value in ca_province_map.iteritems():
			ca_province_name_map[value.lower()] = code

		ca_province_name_map["b.c."] = "bc"
		ca_province_name_map["newfoundland"] = "nl"
		ca_province_name_map["north west territories"] = "nt"
		ca_province_name_map[u"qu\N{LATIN SMALL LETTER E WITH ACUTE}bec"] = "qc"

	return	ca_province_name_map.get(name, otherwise)
	
#
#	Phone Area Codes
#
area_code_map = {
	"684" : {
		"tz" : -11,
		"country" : "AS",
	},
	"264" : {
		"tz" : -4,
		"country" : "AI",
	},
	"268" : {
		"tz" : -4,
		"country" : "AG",
	},
	"246" : {
		"tz" : -4,
		"country" : "BB",
	},
	"441" : {
		"tz" : -4,
		"country" : "BM",
	},
	"284" : {
		"tz" : -4,
		"country" : "VG",
	},
	"767" : {
		"tz" : -4,
		"country" : "DM",
	},
	"809" : {
		"tz" : -4,
		"country" : "DO",
	},
	"590" : {
		"tz" : -4,
		# "country" : "French West Indies Carribean Islands",
	},
	"473" : {
		"tz" : -4,
		"country" : "GD",
	},
	"664" : {
		"tz" : -4,
		"country" : "MS",
	},
	"869" : {
		"tz" : -4,
		"country" : "KN",
	},
	"758" : {
		"tz" : -4,
		"country" : "LC",
	},
	"784" : {
		"tz" : -4,
		"country" : "VC",
	},
	"868" : {
		"tz" : -4,
		"country" : "TT",
	},
	"340" : {
		"tz" : -4,
		"country" : "VI",
	},
	"242" : {
		"tz" : -5,
		"country" : "MS",
	},
	"345" : {
		"tz" : -5,
		"country" : "KY",
	},
	"876" : {
		"tz" : -5,
		"country" : "JM",
	},
	"649" : {
		"tz" : -5,
		"country" : "TC",
	},
	"780" : {
		"state" : "AB",
		"tz" : -7,
		"country" : "CA",
	},
	"403" : {
		"state" : "AB",
		"tz" : -7,
		"country" : "CA",
	},
	"907" : {
		"state" : "AK",
		"tz" : -9,
		"country" : "US",
	},
	"205" : {
		"state" : "AL",
		"tz" : -6,
		"country" : "US",
	},
	"256" : {
		"state" : "AL",
		"tz" : -6,
		"country" : "US",
	},
	"334" : {
		"state" : "AL",
		"tz" : -6,
		"country" : "US",
	},
	"251" : {
		"state" : "AL",
		"tz" : -6,
		"country" : "US",
	},
	"870" : {
		"state" : "AR",
		"tz" : -6,
		"country" : "US",
	},
	"501" : {
		"state" : "AR",
		"tz" : -6,
		"country" : "US",
	},
	"479" : {
		"state" : "AR",
		"tz" : -6,
		"country" : "US",
	},
	"480" : {
		"state" : "AZ",
		"tz" : -7,
		"country" : "US",
	},
	"623" : {
		"state" : "AZ",
		"tz" : -7,
		"country" : "US",
	},
	"928" : {
		"state" : "AZ",
		"tz" : -7,
		"country" : "US",
	},
	"602" : {
		"state" : "AZ",
		"tz" : -8,
		"country" : "US",
		"locality" : "Phoenix",
	},
	"520" : {
		"state" : "AZ",
		"tz" : -8,
		"country" : "US",
	},
	"250" : {
		"state" : "BC",
		"tz" : -8,
		"country" : "CA",
	},
	"778" : {
		"state" : "BC",
		"tz" : -8,
		"country" : "CA",
		"locality" : "Vancouver",
	},
	"604" : {
		"state" : "BC",
		"tz" : -8,
		"country" : "CA",
	},
	"925" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"909" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"562" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"661" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"657" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"510" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"650" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"949" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"760" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"415" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"951" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"752" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"831" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"209" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"669" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"408" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"559" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"626" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"442" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"530" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"916" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"707" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"627" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"714" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"310" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"323" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"213" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
		"locality" : "Los Angeles",
	},
	"424" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"747" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"818" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"858" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"935" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"619" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"805" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"369" : {
		"state" : "CA",
		"tz" : -8,
		"country" : "US",
	},
	"720" : {
		"state" : "CO",
		"tz" : -7,
		"country" : "US",
	},
	"303" : {
		"state" : "CO",
		"tz" : -7,
		"country" : "US",
	},
	"970" : {
		"state" : "CO",
		"tz" : -7,
		"country" : "US",
	},
	"719" : {
		"state" : "CO",
		"tz" : -7,
		"country" : "US",
	},
	"203" : {
		"state" : "CT",
		"tz" : -5,
		"country" : "US",
	},
	"959" : {
		"state" : "CT",
		"tz" : -5,
		"country" : "US",
	},
	"475" : {
		"state" : "CT",
		"tz" : -5,
		"country" : "US",
	},
	"860" : {
		"state" : "CT",
		"tz" : -5,
		"country" : "US",
	},
	"202" : {
		"state" : "DC",
		"tz" : -5,
		"country" : "US",
	},
	"302" : {
		"state" : "DE",
		"tz" : -5,
		"country" : "US",
	},
	"689" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"407" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"239" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"836" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"727" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"321" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"754" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"954" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"352" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"863" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"904" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"386" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"561" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"772" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"786" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"305" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"861" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"941" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"813" : {
		"state" : "FL",
		"tz" : -5,
		"country" : "US",
	},
	"850" : {
		"state" : "FL",
		"tz" : -6,
		"country" : "US",
	},
	"478" : {
		"state" : "GA",
		"tz" : -5,
		"country" : "US",
	},
	"770" : {
		"state" : "GA",
		"tz" : -5,
		"country" : "US",
	},
	"470" : {
		"state" : "GA",
		"tz" : -5,
		"country" : "US",
	},
	"404" : {
		"state" : "GA",
		"tz" : -5,
		"country" : "US",
	},
	"706" : {
		"state" : "GA",
		"tz" : -5,
		"country" : "US",
	},
	"678" : {
		"state" : "GA",
		"tz" : -5,
		"country" : "US",
	},
	"912" : {
		"state" : "GA",
		"tz" : -5,
		"country" : "US",
	},
	"229" : {
		"state" : "GA",
		"tz" : -5,
		"country" : "US",
	},
	"671" : {
		"tz" : 10,
		"country" : "Guam",
	},
	"808" : {
		"state" : "HI",
		"tz" : -10,
		"country" : "US",
	},
	"515" : {
		"state" : "IA",
		"tz" : -6,
		"country" : "US",
	},
	"319" : {
		"state" : "IA",
		"tz" : -6,
		"country" : "US",
	},
	"563" : {
		"state" : "IA",
		"tz" : -6,
		"country" : "US",
	},
	"641" : {
		"state" : "IA",
		"tz" : -6,
		"country" : "US",
	},
	"712" : {
		"state" : "IA",
		"tz" : -6,
		"country" : "US",
	},
	"208" : {
		"state" : "ID",
		"country" : "US",
	},
	"217" : {
		"state" : "IL",
		"tz" : -6,
		"country" : "US",
	},
	"282" : {
		"state" : "IL",
		"tz" : -6,
		"country" : "US",
	},
	"872" : {
		"state" : "IL",
		"tz" : -6,
		"country" : "US",
	},
	"312" : {
		"state" : "IL",
		"tz" : -6,
		"country" : "US",
		"locality" : "Chicago",
	},
	"773" : {
		"state" : "IL",
		"tz" : -6,
		"country" : "US",
		"locality" : "Chicago",
	},
	"464" : {
		"state" : "IL",
		"tz" : -6,
		"country" : "US",
	},
	"708" : {
		"state" : "IL",
		"tz" : -6,
		"country" : "US",
	},
	"815" : {
		"state" : "IL",
		"tz" : -6,
		"country" : "US",
	},
	"224" : {
		"state" : "IL",
		"tz" : -6,
		"country" : "US",
	},
	"847" : {
		"state" : "IL",
		"tz" : -6,
		"country" : "US",
	},
	"618" : {
		"state" : "IL",
		"tz" : -6,
		"country" : "US",
	},
	"309" : {
		"state" : "IL",
		"tz" : -6,
		"country" : "US",
	},
	"331" : {
		"state" : "IL",
		"tz" : -6,
		"country" : "US",
	},
	"630" : {
		"state" : "IL",
		"tz" : -6,
		"country" : "US",
	},
	"765" : {
		"state" : "IN",
		"tz" : -5,
		"country" : "US",
	},
	"574" : {
		"state" : "IN",
		"tz" : -5,
		"country" : "US",
	},
	"260" : {
		"state" : "IN",
		"tz" : -5,
		"country" : "US",
	},
	"219" : {
		"state" : "IN",
		"tz" : -5,
		"country" : "US",
	},
	"317" : {
		"state" : "IN",
		"tz" : -6,
		"country" : "US",
	},
	"812" : {
		"state" : "IN",
		"tz" : -6,
		"country" : "US",
	},
	"913" : {
		"state" : "KS",
		"tz" : -6,
		"country" : "US",
	},
	"785" : {
		"state" : "KS",
		"tz" : -6,
		"country" : "US",
	},
	"316" : {
		"state" : "KS",
		"tz" : -6,
		"country" : "US",
	},
	"620" : {
		"state" : "KS",
		"tz" : -6,
		"country" : "US",
	},
	"327" : {
		"state" : "KY",
		"tz" : -5,
		"country" : "US",
	},
	"502" : {
		"state" : "KY",
		"tz" : -5,
		"country" : "US",
	},
	"859" : {
		"state" : "KY",
		"tz" : -5,
		"country" : "US",
	},
	"606" : {
		"state" : "KY",
		"country" : "US",
	},
	"270" : {
		"state" : "KY",
		"tz" : -6,
		"country" : "US",
	},
	"504" : {
		"state" : "LA",
		"tz" : -6,
		"country" : "US",
	},
	"985" : {
		"state" : "LA",
		"tz" : -6,
		"country" : "US",
	},
	"225" : {
		"state" : "LA",
		"tz" : -6,
		"country" : "US",
	},
	"318" : {
		"state" : "LA",
		"tz" : -6,
		"country" : "US",
	},
	"337" : {
		"state" : "LA",
		"tz" : -6,
		"country" : "US",
	},
	"774" : {
		"state" : "MA",
		"tz" : -5,
		"country" : "US",
	},
	"508" : {
		"state" : "MA",
		"tz" : -5,
		"country" : "US",
	},
	"781" : {
		"state" : "MA",
		"tz" : -5,
		"country" : "US",
	},
	"339" : {
		"state" : "MA",
		"tz" : -5,
		"country" : "US",
	},
	"857" : {
		"state" : "MA",
		"tz" : -5,
		"country" : "US",
	},
	"617" : {
		"state" : "MA",
		"tz" : -5,
		"country" : "US",
	},
	"978" : {
		"state" : "MA",
		"tz" : -5,
		"country" : "US",
	},
	"351" : {
		"state" : "MA",
		"tz" : -5,
		"country" : "US",
	},
	"413" : {
		"state" : "MA",
		"tz" : -5,
		"country" : "US",
	},
	"204" : {
		"state" : "MB",
		"tz" : -6,
		"country" : "CA",
	},
	"443" : {
		"state" : "MD",
		"tz" : -5,
		"country" : "US",
	},
	"410" : {
		"state" : "MD",
		"tz" : -5,
		"country" : "US",
	},
	"280" : {
		"state" : "MD",
		"tz" : -5,
		"country" : "US",
	},
	"249" : {
		"state" : "MD",
		"tz" : -5,
		"country" : "US",
	},
	"969" : {
		"state" : "MD",
		"tz" : -5,
		"country" : "US",
	},
	"240" : {
		"state" : "MD",
		"tz" : -5,
		"country" : "US",
	},
	"301" : {
		"state" : "MD",
		"tz" : -5,
		"country" : "US",
	},
	"207" : {
		"state" : "ME",
		"tz" : -5,
		"country" : "US",
	},
	"383" : {
		"state" : "ME",
		"tz" : -5,
		"country" : "US",
	},
	"517" : {
		"state" : "MI",
		"tz" : -5,
		"country" : "US",
	},
	"546" : {
		"state" : "MI",
		"tz" : -5,
		"country" : "US",
	},
	"810" : {
		"state" : "MI",
		"tz" : -5,
		"country" : "US",
	},
	"278" : {
		"state" : "MI",
		"tz" : -5,
		"country" : "US",
	},
	"313" : {
		"state" : "MI",
		"tz" : -5,
		"country" : "US",
	},
	"586" : {
		"state" : "MI",
		"tz" : -5,
		"country" : "US",
	},
	"248" : {
		"state" : "MI",
		"tz" : -5,
		"country" : "US",
	},
	"734" : {
		"state" : "MI",
		"tz" : -5,
		"country" : "US",
	},
	"269" : {
		"state" : "MI",
		"tz" : -5,
		"country" : "US",
	},
	"906" : {
		"state" : "MI",
		"tz" : -5,
		"country" : "US",
	},
	"989" : {
		"state" : "MI",
		"tz" : -5,
		"country" : "US",
	},
	"616" : {
		"state" : "MI",
		"tz" : -5,
		"country" : "US",
	},
	"231" : {
		"state" : "MI",
		"tz" : -5,
		"country" : "US",
	},
	"947" : {
		"state" : "MI",
		"country" : "US",
	},
	"612" : {
		"state" : "MN",
		"tz" : -6,
		"country" : "US",
	},
	"320" : {
		"state" : "MN",
		"tz" : -6,
		"country" : "US",
	},
	"651" : {
		"state" : "MN",
		"tz" : -6,
		"country" : "US",
	},
	"763" : {
		"state" : "MN",
		"tz" : -6,
		"country" : "US",
	},
	"952" : {
		"state" : "MN",
		"tz" : -6,
		"country" : "US",
	},
	"218" : {
		"state" : "MN",
		"tz" : -6,
		"country" : "US",
	},
	"507" : {
		"state" : "MN",
		"tz" : -6,
		"country" : "US",
	},
	"636" : {
		"state" : "MO",
		"tz" : -6,
		"country" : "US",
	},
	"660" : {
		"state" : "MO",
		"tz" : -6,
		"country" : "US",
	},
	"975" : {
		"state" : "MO",
		"tz" : -6,
		"country" : "US",
	},
	"816" : {
		"state" : "MO",
		"tz" : -6,
		"country" : "US",
	},
	"314" : {
		"state" : "MO",
		"tz" : -6,
		"country" : "US",
	},
	"557" : {
		"state" : "MO",
		"tz" : -6,
		"country" : "US",
	},
	"573" : {
		"state" : "MO",
		"tz" : -6,
		"country" : "US",
	},
	"417" : {
		"state" : "MO",
		"tz" : -6,
		"country" : "US",
	},
	"670" : {
		"state" : "MP",
		"tz" : 10,
		"country" : "US",
	},
	"601" : {
		"state" : "MS",
		"tz" : -6,
		"country" : "US",
	},
	"662" : {
		"state" : "MS",
		"tz" : -6,
		"country" : "US",
	},
	"228" : {
		"state" : "MS",
		"tz" : -6,
		"country" : "US",
	},
	"406" : {
		"state" : "MT",
		"tz" : -7,
		"country" : "US",
	},
	"107" : {
		"state" : "MX",
		"tz" : -6,
		"country" : "US",
	},
	"506" : {
		"state" : "NB",
		"tz" : -4,
		"country" : "CA",
	},
	"336" : {
		"state" : "NC",
		"tz" : -5,
		"country" : "US",
	},
	"252" : {
		"state" : "NC",
		"tz" : -5,
		"country" : "US",
	},
	"984" : {
		"state" : "NC",
		"tz" : -5,
		"country" : "US",
	},
	"919" : {
		"state" : "NC",
		"tz" : -5,
		"country" : "US",
	},
	"980" : {
		"state" : "NC",
		"tz" : -5,
		"country" : "US",
	},
	"910" : {
		"state" : "NC",
		"tz" : -5,
		"country" : "US",
	},
	"828" : {
		"state" : "NC",
		"tz" : -5,
		"country" : "US",
	},
	"704" : {
		"state" : "NC",
		"tz" : -5,
		"country" : "US",
	},
	"701" : {
		"state" : "ND",
		"tz" : -6,
		"country" : "US",
	},
	"402" : {
		"state" : "NE",
		"tz" : -6,
		"country" : "US",
	},
	"308" : {
		"state" : "NE",
		"country" : "US",
	},
	"709" : {
		"state" : "NL",
		"country" : "CA",
	},
	"603" : {
		"state" : "NH",
		"tz" : -5,
		"country" : "US",
	},
	"908" : {
		"state" : "NJ",
		"tz" : -5,
		"country" : "US",
	},
	"848" : {
		"state" : "NJ",
		"tz" : -5,
		"country" : "US",
	},
	"732" : {
		"state" : "NJ",
		"tz" : -5,
		"country" : "US",
	},
	"551" : {
		"state" : "NJ",
		"tz" : -5,
		"country" : "US",
	},
	"201" : {
		"state" : "NJ",
		"tz" : -5,
		"country" : "US",
	},
	"862" : {
		"state" : "NJ",
		"tz" : -5,
		"country" : "US",
	},
	"973" : {
		"state" : "NJ",
		"tz" : -5,
		"country" : "US",
	},
	"609" : {
		"state" : "NJ",
		"tz" : -5,
		"country" : "US",
	},
	"856" : {
		"state" : "NJ",
		"tz" : -5,
		"country" : "US",
	},
	"505" : {
		"state" : "NM",
		"tz" : -7,
		"country" : "US",
	},
	"957" : {
		"state" : "NM",
		"tz" : -7,
		"country" : "US",
	},
	"902" : {
		"state" : "NS",
		"tz" : -4,
		"country" : "CA",
	},
	"702" : {
		"state" : "NV",
		"tz" : -8,
		"country" : "US",
	},
	"775" : {
		"state" : "NV",
		"tz" : -8,
		"country" : "US",
	},
	"315" : {
		"state" : "NY",
		"tz" : -5,
		"country" : "US",
	},
	"518" : {
		"state" : "NY",
		"tz" : -5,
		"country" : "US",
	},
	"716" : {
		"state" : "NY",
		"tz" : -5,
		"country" : "US",
	},
	"585" : {
		"state" : "NY",
		"tz" : -5,
		"country" : "US",
	},
	"646" : {
		"state" : "NY",
		"tz" : -5,
		"country" : "US",
		"locality" : "New York City",
	},
	"347" : {
		"state" : "NY",
		"tz" : -5,
		"country" : "US",
	},
	"718" : {
		"state" : "NY",
		"tz" : -5,
		"country" : "US",
	},
	"212" : {
		"state" : "NY",
		"tz" : -5,
		"country" : "US",
		"locality" : "New York City",
	},
	"516" : {
		"state" : "NY",
		"tz" : -5,
		"country" : "US",
	},
	"917" : {
		"state" : "NY",
		"tz" : -5,
		"country" : "US",
		"locality" : "New York City",
	},
	"845" : {
		"state" : "NY",
		"tz" : -5,
		"country" : "US",
	},
	"631" : {
		"state" : "NY",
		"tz" : -5,
		"country" : "US",
	},
	"607" : {
		"state" : "NY",
		"tz" : -5,
		"country" : "US",
	},
	"914" : {
		"state" : "NY",
		"tz" : -5,
		"country" : "US",
	},
	"216" : {
		"state" : "OH",
		"tz" : -5,
		"country" : "US",
	},
	"330" : {
		"state" : "OH",
		"tz" : -5,
		"country" : "US",
	},
	"234" : {
		"state" : "OH",
		"tz" : -5,
		"country" : "US",
	},
	"567" : {
		"state" : "OH",
		"tz" : -5,
		"country" : "US",
	},
	"419" : {
		"state" : "OH",
		"tz" : -5,
		"country" : "US",
	},
	"380" : {
		"state" : "OH",
		"tz" : -5,
		"country" : "US",
	},
	"440" : {
		"state" : "OH",
		"tz" : -5,
		"country" : "US",
	},
	"740" : {
		"state" : "OH",
		"tz" : -5,
		"country" : "US",
	},
	"614" : {
		"state" : "OH",
		"tz" : -5,
		"country" : "US",
	},
	"283" : {
		"state" : "OH",
		"tz" : -5,
		"country" : "US",
	},
	"513" : {
		"state" : "OH",
		"tz" : -5,
		"country" : "US",
	},
	"937" : {
		"state" : "OH",
		"tz" : -5,
		"country" : "US",
	},
	"918" : {
		"state" : "OK",
		"tz" : -6,
		"country" : "US",
	},
	"580" : {
		"state" : "OK",
		"tz" : -6,
		"country" : "US",
	},
	"405" : {
		"state" : "OK",
		"tz" : -6,
		"country" : "US",
	},
	"705" : {
		"state" : "ON",
		"tz" : -5,
		"country" : "CA",
	},
	"289" : {
		"state" : "ON",
		"tz" : -5,
		"country" : "CA",
	},
	"905" : {
		"state" : "ON",
		"tz" : -5,
		"country" : "CA",
	},
	"647" : {
		"state" : "ON",
		"tz" : -5,
		"country" : "CA",
		"locality" : "Toronto",
	},
	"416" : {
		"state" : "ON",
		"tz" : -5,
		"country" : "CA",
		"locality" : "Toronto",
	},
	"613" : {
		"state" : "ON",
		"tz" : -5,
		"country" : "CA",
	},
	"519" : {
		"state" : "ON",
		"tz" : -5,
		"country" : "CA",
	},
	"807" : {
		"state" : "ON",
		"country" : "CA",
	},
	"503" : {
		"state" : "OR",
		"tz" : -8,
		"country" : "US",
	},
	"971" : {
		"state" : "OR",
		"tz" : -8,
		"country" : "US",
	},
	"541" : {
		"state" : "OR",
		"tz" : -8,
		"country" : "US",
	},
	"814" : {
		"state" : "PA",
		"tz" : -5,
		"country" : "US",
	},
	"717" : {
		"state" : "PA",
		"tz" : -5,
		"country" : "US",
	},
	"570" : {
		"state" : "PA",
		"tz" : -5,
		"country" : "US",
	},
	"358" : {
		"state" : "PA",
		"tz" : -5,
		"country" : "US",
	},
	"878" : {
		"state" : "PA",
		"tz" : -5,
		"country" : "US",
	},
	"835" : {
		"state" : "PA",
		"tz" : -5,
		"country" : "US",
	},
	"484" : {
		"state" : "PA",
		"tz" : -5,
		"country" : "US",
	},
	"610" : {
		"state" : "PA",
		"tz" : -5,
		"country" : "US",
	},
	"445" : {
		"state" : "PA",
		"tz" : -5,
		"country" : "US",
	},
	"267" : {
		"state" : "PA",
		"tz" : -5,
		"country" : "US",
	},
	"215" : {
		"state" : "PA",
		"tz" : -5,
		"country" : "US",
	},
	"724" : {
		"state" : "PA",
		"tz" : -5,
		"country" : "US",
	},
	"412" : {
		"state" : "PA",
		"tz" : -5,
		"country" : "US",
	},
	"939" : {
		"tz" : -4,
		"country" : "Puerto Rico",
	},
	"787" : {
		"tz" : -4,
		"country" : "Puerto Rico",
	},
	"438" : {
		"state" : "QC",
		"tz" : -5,
		"country" : "CA",
	},
	"514" : {
		"state" : "QC",
		"tz" : -5,
		"country" : "CA",
	},
	"819" : {
		"state" : "QC",
		"tz" : -5,
		"country" : "CA",
	},
	"418" : {
		"state" : "QC",
		"country" : "CA",
	},
	"450" : {
		"state" : "QC",
		"country" : "CA",
	},
	"401" : {
		"state" : "RI",
		"tz" : -5,
		"country" : "US",
	},
	"843" : {
		"state" : "SC",
		"tz" : -5,
		"country" : "US",
	},
	"864" : {
		"state" : "SC",
		"tz" : -5,
		"country" : "US",
	},
	"803" : {
		"state" : "SC",
		"tz" : -5,
		"country" : "US",
	},
	"605" : {
		"state" : "SD",
		"country" : "US",
	},
	"306" : {
		"state" : "SK",
		"country" : "CA",
	},
	"423" : {
		"state" : "TN",
		"tz" : -5,
		"country" : "US",
	},
	"865" : {
		"state" : "TN",
		"tz" : -5,
		"country" : "US",
	},
	"931" : {
		"state" : "TN",
		"tz" : -6,
		"country" : "US",
	},
	"615" : {
		"state" : "TN",
		"tz" : -6,
		"country" : "US",
	},
	"901" : {
		"state" : "TN",
		"tz" : -6,
		"country" : "US",
	},
	"731" : {
		"state" : "TN",
		"tz" : -6,
		"country" : "US",
	},
	"254" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"325" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"713" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"940" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"817" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"430" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"903" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"806" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"737" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"512" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"361" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"210" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"936" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"409" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"979" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"972" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"469" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"214" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"682" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"832" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"281" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"830" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"956" : {
		"state" : "TX",
		"tz" : -6,
		"country" : "US",
	},
	"432" : {
		"state" : "TX",
		"country" : "US",
	},
	"915" : {
		"state" : "TX",
		"country" : "US",
	},
	"435" : {
		"state" : "UT",
		"tz" : -7,
		"country" : "US",
	},
	"801" : {
		"state" : "UT",
		"tz" : -7,
		"country" : "US",
	},
	"385" : {
		"state" : "UT",
		"tz" : -7,
		"country" : "US",
	},
	"434" : {
		"state" : "VA",
		"tz" : -5,
		"country" : "US",
	},
	"804" : {
		"state" : "VA",
		"tz" : -5,
		"country" : "US",
	},
	"757" : {
		"state" : "VA",
		"tz" : -5,
		"country" : "US",
	},
	"703" : {
		"state" : "VA",
		"tz" : -5,
		"country" : "US",
	},
	"571" : {
		"state" : "VA",
		"tz" : -5,
		"country" : "US",
	},
	"540" : {
		"state" : "VA",
		"tz" : -5,
		"country" : "US",
	},
	"276" : {
		"state" : "VA",
		"tz" : -5,
		"country" : "US",
	},
	"381" : {
		"state" : "VA",
		"tz" : -5,
		"country" : "US",
	},
	"236" : {
		"state" : "VA",
		"tz" : -5,
		"country" : "US",
	},
	"802" : {
		"state" : "VT",
		"tz" : -5,
		"country" : "US",
	},
	"509" : {
		"state" : "WA",
		"tz" : -8,
		"country" : "US",
	},
	"360" : {
		"state" : "WA",
		"tz" : -8,
		"country" : "US",
	},
	"564" : {
		"state" : "WA",
		"tz" : -8,
		"country" : "US",
	},
	"206" : {
		"state" : "WA",
		"tz" : -8,
		"country" : "US",
	},
	"425" : {
		"state" : "WA",
		"tz" : -8,
		"country" : "US",
	},
	"253" : {
		"state" : "WA",
		"tz" : -8,
		"country" : "US",
	},
	"715" : {
		"state" : "WI",
		"tz" : -6,
		"country" : "US",
	},
	"920" : {
		"state" : "WI",
		"tz" : -6,
		"country" : "US",
	},
	"414" : {
		"state" : "WI",
		"tz" : -6,
		"country" : "US",
	},
	"262" : {
		"state" : "WI",
		"tz" : -6,
		"country" : "US",
	},
	"608" : {
		"state" : "WI",
		"tz" : -6,
		"country" : "US",
	},
	"353" : {
		"state" : "WI",
		"tz" : -6,
		"country" : "US",
	},
	"420" : {
		"state" : "WI",
		"tz" : -6,
		"country" : "US",
	},
	"304" : {
		"state" : "WV",
		"tz" : -5,
		"country" : "US",
	},
	"307" : {
		"state" : "WY",
		"tz" : -7,
		"country" : "US",
	},
	"867" : {
		"state" : "YT",
		"country" : "CA",
	},
}
def area_code(code):
	m = area_code_map.get(str(code))
	if not m:
		return	None

	country = m.get("country")
	if country:
		country_name = country_map.get(country.upper())
		if country_name:
			m["country_name"] = country_name

		
	state = m.get("state")

	if country == "CA" and state:
		state_name = ca_province_map.get(state.lower())
		if state_name:
			m["state_name"] = state_name

	if country == "US" and state:
		state_name = us_state_map.get(state.lower())
		if state_name:
			m["state_name"] = state_name

	return	m

itu_calling_code_map = {
	"93" : "AF",
	"355" : "AL",
	"213" : "DZ",
	"376" : "AD",
	"244" : "AO",
	"54" : "AR",
	"7" : "AM",
	"297" : "AW",
	"61" : "AU",
	"43" : "AT",
	"994" : "AZ",
	"973" : "BH",
	"880" : "BD",
	"375" : "BY",
	"32" : "BE",
	"501" : "BZ",
	"229" : "BJ",
	"975" : "BT",
	"591" : "BO",
	"387" : "BA",
	"267" : "BW",
	"55" : "BR",
	"673" : "BN",
	"359" : "BG",
	"226" : "BF",
	"257" : "BI",
	"855" : "KH",
	"237" : "CM",
	"238" : "CV",
	"236" : "CF",
	"235" : "TD",
	"56" : "CL",
	"86" : "CN",
	"57" : "CO",
	"269" : "KM",
	"242" : "CG",
	"243" : "CD",
	"682" : "CK",
	"506" : "CR",
	"225" : "CI",
	"385" : "HR",
	"53" : "CU",
	"357" : "CY",
	"420" : "CZ",
	"45" : "DK",
	"253" : "DJ",
	"593" : "EC",
	"20" : "EG",
	"503" : "SV",
	"240" : "GQ",
	"291" : "ER",
	"372" : "EE",
	"251" : "ET",
	"298" : "FO",
	"500" : "FK",
	"679" : "FJ",
	"358" : "FI",
	"33" : "FR",
	"594" : "GF",
	"689" : "PF",
	"241" : "GA",
	"220" : "GM",
	"49" : "DE",
	"233" : "GH",
	"350" : "GI",
	"44" : "GB",
	"30" : "GR",
	"299" : "GL",
	"590" : "GP",
	"502" : "GT",
	"224" : "GN",
	"245" : "GW",
	"592" : "GY",
	"509" : "HT",
	"504" : "HN",
	"852" : "HK",
	"36" : "HU",
	"354" : "IS",
	"91" : "IN",
	"62" : "ID",
	"98" : "IR",
	"964" : "IQ",
	"353" : "IE",
	"972" : "IL",
	"39" : "IT",
	"81" : "JP",
	"962" : "JO",
	"254" : "KE",
	"686" : "KI",
	"408" : "a)",
	"82" : "KR",
	"965" : "KW",
	"996" : "KG",
	"856" : "LA",
	"371" : "LV",
	"961" : "LB",
	"266" : "LS",
	"231" : "LR",
	"218" : "LY",
	"423" : "LI",
	"370" : "LT",
	"352" : "LU",
	"853" : "MO",
	"389" : "MK",
	"261" : "MG",
	"265" : "MW",
	"60" : "MY",
	"960" : "MV",
	"223" : "ML",
	"356" : "MT",
	"692" : "MH",
	"596" : "MQ",
	"222" : "MR",
	"230" : "MU",
	"269" : "YT",
	"52" : "MX",
	"691" : "FM",
	"373" : "MD",
	"377" : "MC",
	"976" : "MN",
	"212" : "MA",
	"258" : "MZ",
	"95" : "MM",
	"674" : "NR",
	"977" : "NP",
	"31" : "NL",
	"599" : "AN",
	"687" : "NC",
	"64" : "NZ",
	"505" : "NI",
	"227" : "NE",
	"234" : "NG",
	"683" : "NU",
	"47" : "NO",
	"968" : "OM",
	"92" : "PK",
	"680" : "PW",
	"970" : "PS",
	"507" : "PA",
	"675" : "PG",
	"595" : "PY",
	"51" : "PE",
	"63" : "PH",
	"48" : "PL",
	"351" : "PT",
	"974" : "QA",
	"262" : "RE",
	"40" : "RO",
	"7" : "RU",
	"250" : "RW",
	"290" : "SH",
	"508" : "PM",
	"685" : "WS",
	"378" : "SM",
	"239" : "ST",
	"966" : "SA",
	"221" : "SN",
	"381" : "CS",
	"248" : "SC",
	"232" : "SL",
	"65" : "SG",
	"421" : "SK",
	"386" : "SI",
	"677" : "SB",
	"252" : "SO",
	"27" : "ZA",
	"34" : "ES",
	"94" : "LK",
	"249" : "SD",
	"597" : "SR",
	"268" : "SZ",
	"46" : "SE",
	"41" : "CH",
	"963" : "SY",
	"886" : "TW",
	"992" : "TJ",
	"255" : "TZ",
	"66" : "TH",
	"670" : "TL",
	"228" : "TG",
	"690" : "TK",
	"676" : "TO",
	"216" : "TN",
	"90" : "TR",
	"993" : "TM",
	"688" : "TV",
	"256" : "UG",
	"380" : "UA",
	"971" : "AE",
	"44" : "GB",
	"598" : "UY",
	"998" : "UZ",
	"678" : "VU",
	"379" : "VA",
	"58" : "VE",
	"84" : "VN",
	"681" : "WF",
	"967" : "YE",
	"260" : "ZM",
	"263" : "ZW",
}

def itu_calling_code(code):
	country = itu_calling_code_map.get(str(code))
	if not country:
		return	None

	country_name = country_map.get(country.upper())
	if not country_name:
		return	None

	return	{
		"itu" : str(code),
		"country" : country,
		"country_name" : country_name,
	}

