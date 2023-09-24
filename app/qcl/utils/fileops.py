import tempfile
import os

def create_tempfile(content: str):
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False) as tmpfile:
        # Write the code string to the temp file
        tmpfile.write(content)
        tmpfile_name = tmpfile.name
    return tmpfile_name

def delete_file(filename: str):
    os.unlink(filename)