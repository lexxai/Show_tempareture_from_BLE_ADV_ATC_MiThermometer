from pathlib import Path


def get_version(pyproject: str = None):
    version = "0.1.0-dev"
    if not pyproject:
        pyproject = Path(__file__).parent.parent.joinpath("pyproject.toml")

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


__version__ = get_version()
