@echo off

SETLOCAL ENABLEDELAYEDEXPANSION
poetry --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Poetry is installed.
    SET RUNNER=poetry run
) else (
    echo Poetry is not installed.
    SET RUNNER=""
)


%RUNNER% python ./build_version.py

mkdir "../pyinstall"
ERASE "../pyinstall" /S/Q
pushd "../pyinstall"


SET PYTHONPATH=%PYTHONPATH%;../MiTermometerPVVX
%RUNNER% pyinstaller --clean ../MiTermometerPVVX/main.py ^
  --name MiTermometerPVVX --onefile --collect-all winrt --collect-all plyer ^
  --version-file ../versionfile.txt ^
  --icon ../icon-64x64.ico --add-data=../icon-64x64.ico;. --add-data=../pyproject.toml;.

popd