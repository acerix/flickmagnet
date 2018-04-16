
=  Building Flick Magnet for Windows =

Port btfs to Windows and install it

  https://github.com/johang/btfs

Install Python 3

    https://www.python.org/downloads/windows/

Install Flick Magnet

  https://github.com/acerix/flickmagnet/archive/master.zip

    python.exe setup.py install

Install PyInstaller

    pip.exe install pyinstaller

    http://www.pyinstaller.org/

Build package with PyInstaller

    pyinstaller.exe --onefile --upx-dir=\upx391w --icon=htdocs/favicon.ico flickmagnet.py

    Install upx for a compressed binary, dir specified in: --upx-dir
