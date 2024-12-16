@echo off
pushd ".."
poetry export --without-hashes --without=dev  > requirements.txt
POPD