import pyinstaller_versionfile


version = "0.1.0"
try:
    with open('../pyproject.toml') as f:
        for line in f:
            if not "=" in line:
                continue
            key, value = line.strip().split('=', 1)
            if key.strip() == 'version':
                version = value.strip().strip('"')
                break
except FileNotFoundError:
    ...


pyinstaller_versionfile.create_versionfile(
    output_file="versionfile.txt",
    version=f"{version}.0",
    # version="0.1.0.0",
    company_name="lexxai",
    file_description='Show temperature and humidity from BLE ADV "ATC MiThermometer" (PVVX)',
    internal_name="MiTermometerPVVX",
    legal_copyright="https://github.com/lexxai/Show_temperature_from_BLE_ADV_ATC_MiThermometer",
    original_filename="MiTermometerPVVX.exe",
    product_name="MiTermometerPVVX"

)
