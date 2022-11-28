import pyinstaller_versionfile

pyinstaller_versionfile.create_versionfile(
    output_file="versionfile.txt",
    version="0.1.0.0",
    company_name="lexxai",
    file_description='Show temperature and humidity from BLE ADV "ATC MiThermometer" (PVVX)',
    internal_name="MiTermometerPVVX",
    legal_copyright="https://github.com/lexxai/Show_temperature_from_BLE_ADV_ATC_MiThermometer",
    original_filename="MiTermometerPVVX.exe",
    product_name="MiTermometerPVVX"
)
