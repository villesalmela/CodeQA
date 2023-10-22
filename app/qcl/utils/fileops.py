import tempfile
import os


def create_tempfile(content: str):
    "Create a temporary file with .py extension, and return its name."

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as tmpfile:
        tmpfile.write(content)
        tmpfile_name = tmpfile.name
    return tmpfile_name


def delete_file(filename: str):
    os.unlink(filename)
