import subprocess
from typing import List
from langchain_core.tools import tool


@tool
def add_dependencies(dependencies: List[str]) -> str:
    """
    Installs Python packages from PyPI into the current environment.

    Uses the 'uv' package manager to add specified dependencies. Each package
    name must correspond to a valid PyPI package identifier.

    Parameters:
        dependencies (List[str]):
            List of package names to install (e.g., ["requests", "numpy"])

    Returns:
        str:
            Status message indicating installation success or failure details
    """

    try:
        # Execute installation command
        subprocess.check_call(
            ["uv", "add"] + dependencies,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        package_list = ", ".join(dependencies)
        return f"Successfully installed dependencies: {package_list}"
    
    except subprocess.CalledProcessError as error:
        # Handle installation failures
        return (
            "Dependency installation failed.\n"
            f"Exit code: {error.returncode}\n"
            f"Error: {error.stderr or 'No error output.'}"
        )
    
    except Exception as error:
        # Handle unexpected errors
        return f"Unexpected error while installing dependencies: {error}" 
