
=  Building Flick Magnet for Windows =

Install Visual C++ 2008 (9.0)

    https://go.microsoft.com/?linkid=7729279
    
    This is required for boost

Install Python 2

    https://www.python.org/downloads/windows/
    
    Python 3 should also work, if you can get libtorrent installed...

Install boost

    http://www.boost.org/users/download/#live
    
    Create a text file user-config.jam in %HOMEDRIVE%%HOMEPATH%, and specify the compiler:
	
		using msvc: 9.0;

Install py-libtorrent

    This should get installed by setup.py, if boost and python2 are installed first

    http://sourceforge.net/projects/libtorrent/files/py-libtorrent/

Install Flick Magnet

	https://github.com/acerix/flickmagnet/archive/master.zip

    \python27\python.exe setup.py install --optimize=1

Install PyInstaller

    pip install pyinstaller
    
    http://www.pyinstaller.org/

Build package with PyInstaller

    pyinstaller --onefile --icon=htdocs/favicon.ico --upx-dir=\upx391w flickmagnet.py

    Install upx for a compressed binary, dir specified in: --upx-dir
