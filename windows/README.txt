=  Flick Magnet Installer for Windows =

Install Visual C++

    (not free)

Install Python 2

    https://www.python.org/downloads/windows/

Install py-libtorrent

    This should get installed by setup.py, requires boost and python2

    http://sourceforge.net/projects/libtorrent/files/py-libtorrent/

Install Flick Magnet

    \Python27\python.exe setup.py install --optimize=1

Install PyInstaller with pip

    pip install pyinstaller

    http://www.pyinstaller.org/

Build with PyInstaller

    pyinstaller --onefile --icon=htdocs/favicon.ico flickmagnet.py
