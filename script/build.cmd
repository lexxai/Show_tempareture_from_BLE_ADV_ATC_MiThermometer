mkdir "../pyinstall"
ERASE "../pyinstall" /S/Q
cd ../pyinstall

pyinstaller --clean ../MiTermometerPVVX/main.py --name MiTermometerPVVX --onefile --version-file ../versionfile.txt 
