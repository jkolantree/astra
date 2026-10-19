"""Executable package-local identity; historical root version is unchanged."""
import json
from pathlib import Path
VERSION = "1.1.0-alpha.1"
if __name__ == "__main__":
    print((Path(__file__).with_name("VERSION.json")).read_text(), end="")
