import os
from langchain_core.tools import Tool


def read_file_tool(path: str):
    """Read the contents of a file. Input: file path. Returns file contents or directory listing."""
    if not os.path.exists(path):
        return f"Error: Path does not exist: {path}"

    if os.path.isdir(path):
        try:
            contents = os.listdir(path)
            return f"Directory: {path}\nContents:\n" + "\n".join(f"  {item}" for item in sorted(contents))
        except Exception as e:
            return f"Error reading directory: {e}"

    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


def write_file_tool(input_data: str):
    """Write content to a file. Input format: 'path::content' (path and content separated by ::). Creates parent directories if needed."""
    try:
        if "::" not in input_data:
            return "Error: Input must be in format 'path::content'"

        path, content = input_data.split("::", 1)

        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

        with open(path, "w") as f:
            f.write(content)

        return f"Successfully wrote {len(content)} characters to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


file_tools = [
    Tool(
        name="read_file",
        func=read_file_tool,
        description="Read the contents of a file or list a directory. Input: file or directory path.",
    ),
    Tool(
        name="write_file",
        func=write_file_tool,
        description="Write content to a file. Input format: 'path::content' (path and content separated by ::). Creates parent directories if needed.",
    ),
]