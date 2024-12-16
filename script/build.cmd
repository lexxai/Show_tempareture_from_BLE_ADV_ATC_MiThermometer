SET RUNNER=poetry run
%RUNNER% python ./build-version.py

mkdir "../pyinstall"
ERASE "../pyinstall" /S/Q
pushd "../pyinstall"


SET PYTHONPATH=%PYTHONPATH%;../MiTermometerPVVX
%RUNNER% pyinstaller --clean ../MiTermometerPVVX/main.py --name MiTermometerPVVX --onefile --collect-all winrt --version-file ../versionfile.txt
popd