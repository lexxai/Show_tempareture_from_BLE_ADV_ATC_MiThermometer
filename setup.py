from setuptools import setup
import os

base_dir = os.path.dirname(__file__)

setup(
    name="MiTermometerPVVX",
    version="0.1.0",
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
    install_requires=[
        "bleak", "html2text", "importlib_resources"
    ],
    setup_requires="setuptools",
    entry_points={"console_scripts": ["MiTermometerPVVX=MiTermometerPVVX.main:entry_point"]},
    scripts=['MiTermometerPVVX/main.py']
)
