import os

def file_reader(path: str) -> str:
    """Read and return content from a file."""
    if not os.path.exists(path):
        return f"Error: File '{path}' does not exist."
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file '{path}': {str(e)}"

def file_writer(path: str, content: str) -> str:
    """Write string content to disk."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {path}."
    except Exception as e:
        return f"Error writing file '{path}': {str(e)}"
