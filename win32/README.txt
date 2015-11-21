=  Flick Magnet Installer for Windows =

Instructions for building the NSIS Installer for Windows.

== Dependencies ==
 * Bbfreeze: http://pypi.python.org/pypi/bbfreeze
 * NSIS: http://nsis.sourceforge.net/Download

== Build Steps ==

 1.  Build and Install Deluge on Windows.

 2.  Run the bbfreeze script from the win32 directory:

        python flickmagnet-bbfreeze.py

    The result is a bbfreeze'd version in `build-win32`.

 3.  Run the NSIS script (right-click and choose `Compile with NSIS`)

    The result is a standalone installer in the `build-win32` directory.

