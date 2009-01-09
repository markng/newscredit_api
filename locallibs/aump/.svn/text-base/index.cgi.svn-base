#!/bin/sh

if [ "$IROOT" = "" ] 
then
	IROOT="$HOME"
	export IROOT
fi

export PATH="$IROOT/bin:$PATH"

python webservice.py --header --cgi 2> /dev/null


