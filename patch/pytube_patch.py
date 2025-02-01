import os
import sys
import shutil
from pathlib import Path


interpreter_path = sys.executable
python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

PATCH_SCRIPT_FILEPATH = os.path.relpath(__file__)
INCORRECT_FILE_FILEPATH = os.path.join(
    os.path.dirname(interpreter_path), 
    '..',  # Navigate up one directory level
    'lib',
    f'python{python_version}',  # Dynamically include Python version
    'site-packages', 
    'pytube', 
    'cipher.py'
)
CORRECTED_FILE_FILEPATH = os.path.join(
    Path(os.path.relpath(__file__)).parent,
    Path(INCORRECT_FILE_FILEPATH).name
)

def is_pytube_patched():
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