=  Building Flick Magnet for Windows =

Install Visual C++ 2008 (9.0)

    https://go.microsoft.com/?linkid=7729279
    
    This is required for boost

Install Python 2

    https://www.python.org/downloads/windows/
    
    Python 3 should also work, if you can get libtorrent installed

Install py-libtorrent

    This should get installed by setup.py, requires boost and python2

    http://sourceforge.net/projects/libtorrent/files/py-libtorrent/

Install Flick Magnet

	https://github.com/acerix/flickmagnet/archive/master.zip

    \python27\python.exe setup.py install --optimize=1

Install PyInstaller

    pip install pyinstaller
    
    http://www.pyinstaller.org/

Build package with PyInstaller

    pyinstaller --onefile --icon=htdocs/favicon.ico --upx-dir=\upx391w flickmagnet.py

    Install upx for a compressed binary, may need to specify it, eg: --upx-dir=\upx391w
