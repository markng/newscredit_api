FILES=$(echo *.py *.cgi README .htaccess resources)
VERSION=$(date "+%Y%m%d")
DIR=aumfp-$VERSION 

rm -rf $DIR
mkdir $DIR || exit 1

cat > $DIR/QINSTALL.sh << EOF
cd ..
[ -L aumfp ] && rm aumfp
if [ ! -e aumfp ]
then
	ln -s $DIR aumfp
fi
EOF

cp -R $FILES $DIR
tar --exclude "*.svn" -zcf $DIR.tar.gz $DIR

cp ../pybm/bm_*.py $DIR || exit 1
tar --exclude "*.svn" -zcf $DIR-all.tar.gz $DIR

rm -rf $DIR
