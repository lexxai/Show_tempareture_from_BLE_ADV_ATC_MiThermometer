import pyinstaller_versionfile


def get_version(pyproject: str = "../pyproject.toml"):
    version = "0.1.0"
    try:
        with open(pyproject) as f:
            for line in f:
                if not "=" in line:
                    continue
                key, value = line.strip().split("=", 1)
                if key.strip() == "version":
                    version = value.strip().strip('"')
                    break
    except FileNotFoundError:
        ...
    return version


if __name__ == "__main__":
    pyinstaller_versionfile.create_versionfile(
        output_file="../versionfile.txt",
        version=f"{get_version()}.0",
        # version="0.1.0.0",
        company_name="lexxai",
        file_description="Show metrics from BLE devices and notifications",
        internal_name="MiTermometerPVVX",
        legal_copyright="https://github.com/lexxai/Show_temperature_from_BLE_ADV_ATC_MiThermometer",
        original_filename="MiTermometerPVVX.exe",
        product_name="MiTermometerPVVX",
    )
