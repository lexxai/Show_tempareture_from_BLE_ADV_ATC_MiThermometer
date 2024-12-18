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


__version__ = get_version()
