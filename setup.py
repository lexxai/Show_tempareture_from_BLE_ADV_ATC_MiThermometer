from setuptools import setup
import os

from script.build_version import get_version


base_dir = os.path.dirname(__file__)

try:
    install_requires=[i.strip() for i in open("requirements.txt").readlines()],
except FileNotFoundError:
    print("requirements.txt not found, please run script gen_req_txt for generate requirements.txt file")
    exit(1)

version=get_version("./pyproject.toml")

setup(
    name="MiTermometerPVVX",
    version=version,
    description="Show temperature and humidity from BLE ADV 'ATC MiThermometer'",
    long_description="README",
    long_description_content_type="text/markdown",
    url="https://github.com/lexxai/Show_temperature_from_BLE_ADV_ATC_MiThermometer",
    author="lexxai",
    author_email="lexxai@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    packages=["MiTermometerPVVX"],
    include_package_data=True,
    install_requires=install_requires,
    setup_requires="setuptools",
    entry_points={"console_scripts": ["MiTermometerPVVX=MiTermometerPVVX.main:entry_point"]},
    scripts=['MiTermometerPVVX/main.py']
)
