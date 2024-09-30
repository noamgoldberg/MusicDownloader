import os
import sys
import shutil
from pathlib import Path
import importlib.util

# Get the Python interpreter path
interpreter_path = sys.executable
python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

# Get the file path of the current script
PATCH_SCRIPT_FILEPATH = os.path.relpath(__file__)

# Dynamically find the pytube package location
pytube_spec = importlib.util.find_spec('pytube')
if pytube_spec is None:
    raise ImportError("pytube package is not installed.")
else:
    PYTUBE_PACKAGE_DIR = os.path.dirname(pytube_spec.origin)

# Define the path to the incorrect and corrected files
INCORRECT_FILE_FILEPATH = os.path.join(PYTUBE_PACKAGE_DIR, 'cipher.py')
CORRECTED_FILE_FILEPATH = os.path.join(Path(PATCH_SCRIPT_FILEPATH).parent, 'cipher.py')
print("INCORRECT_FILE_FILEPATH:", INCORRECT_FILE_FILEPATH)
print("CORRECTED_FILE_FILEPATH:", CORRECTED_FILE_FILEPATH)

def is_pytube_patched():
    print(f"PYTUBE_PACKAGE_DIR: {PYTUBE_PACKAGE_DIR}")
    print(f"os.listdir(PYTUBE_PACKAGE_DIR): {os.listdir(PYTUBE_PACKAGE_DIR)}")
    print(f"INCORRECT FILE FILEPATH: {INCORRECT_FILE_FILEPATH}")
    with open(INCORRECT_FILE_FILEPATH, "r") as f:
        file_content = f.read()
    return "patch" in file_content

def patch():
    if is_pytube_patched():
        print(f"Package (pytube) already patched: {INCORRECT_FILE_FILEPATH}")
    else:
        shutil.copy(CORRECTED_FILE_FILEPATH, INCORRECT_FILE_FILEPATH)
        print(f"Patch successful. Corrected file {CORRECTED_FILE_FILEPATH} copied to pytube package {INCORRECT_FILE_FILEPATH}")

if __name__ == "__main__":
    patch()
