#! /bin/sh
pushd ../../src
pyinstaller Zamp.spec --distpath=../dist/Mac64/dist --clean -y
# Store the version
ZAMP_VERSION=$(cat version)
popd

pushd ./dist
hdiutil create ./Zamp-$ZAMP_VERSION-Mac64.dmg -srcfolder Zamp.app -ov
popd
