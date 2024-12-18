#!/bin/bash

RUNNER="poetry run"

$RUNNER python ./build_version.py

rm -R "../pyinstall" 
mkdir -p "../pyinstall"
pushd "../pyinstall"


export PYTHONPATH=../MiTermometerPVVX
echo $PYTHONPATH
$RUNNER pyinstaller --clean ../MiTermometerPVVX/main.py --name MiTermometerPVVX --onefile -w -c
popd