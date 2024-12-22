#!/bin/bash

RUNNER="poetry run"

$RUNNER python ./build_version.py
ENVFILE="../.env"

rm -R "../pyinstall" 
mkdir -p "../pyinstall"
pushd "../pyinstall"


export PYTHONPATH=../MiTermometerPVVX
echo $PYTHONPATH
$RUNNER pyinstaller --clean ../MiTermometerPVVX/main.py \
    --icon ../icon-64x64.png \
    --add-data=../icon-64x64.png:. \
    --add-data=../pyproject.toml:. \
    --collect-all pync --name MiTermometerPVVX \
    --onefile -w -c

if [ -f "${ENVFILE}" ] && [ -d "dist" ] ; then
    echo "Copy ${ENVFILE} to dist/"
    cp "${ENVFILE}" dist/
fi 
popd