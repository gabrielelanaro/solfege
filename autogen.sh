#!/bin/bash
set -e

# To run this script on MS Windows you might have to check that the
# paths for PKG_CONFIG_PATH and ACLOCAL_INCLUDE is correctly.
if [ "$OSTYPE" = "msys" ]; then
    export PKG_CONFIG_PATH=/c/GTK/lib/pkgconfig:/c/python25/lib/pkgconfig
    export ACLOCAL_INCLUDE=" -I /c/GTK/share/aclocal"
fi


aclocal $ACINCLUDE

autoconf
if [ "$HOSTNAME" = "gandiserver" ]; then
    export CONFIGURE_OPTS="XML2PO=/home/buildbot/bin/xml2po --disable-pygtk-test"
fi

./configure $CONFIGURE_OPTS

make solfege/_version.py
make solfege/languages.py
make graphics/solfege.png || true
if test ! -e graphics/solfege.png; then
  echo "This error is non-fatal. You will just get one more error message"
  echo "at startup that you can ignore. rsvg is probably missing."
fi

echo
echo "You can now run solfege with no further action from the source directory."
echo "The user manual and some lesson files will be missing until you build it"
echo "by running 'make'. The missing lesson files will generate some warnings"
echo "that you should ignore. Don't report them as bugs!"
