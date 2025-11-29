import subprocess
import os
from langchain_core.tools import tool
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client()

def strip_code_fences(code: str) -> str:
    """Remove markdown code block delimiters if present."""
    code = code.strip()
    # Strip opening fence (```python or ```)
    if code.startswith("```"):
        code = code.split("\n", 1)[1]
    # Strip closing fence
    if code.endswith("```"):
        code = code.rsplit("\n", 1)[0]
    return code.strip()

@tool
def run_code(code: str) -> dict:
    """
    Executes Python source code in an isolated subprocess environment.
    
    Workflow:
      1. Receives Python code as string input
      2. Saves code to a temporary Python file
      3. Runs the file using subprocess
      4. Captures and returns output, errors, and exit status

    Parameters
    ----------
    code : str
        Valid Python source code to be executed

    Returns
    -------
    dict
        Dictionary containing:
        - stdout: Standard output from execution
        - stderr: Error messages if any
        - return_code: Process exit code
    """
    try: 
        script_name = "runner.py"
        work_dir = "LLMFiles"
        
        # Ensure output directory exists
        os.makedirs(work_dir, exist_ok=True)
        
        # Write code to file
        script_path = os.path.join(work_dir, script_name)
        with open(script_path, "w") as code_file:
            code_file.write(code)

        # Execute in subprocess
        process = subprocess.Popen(
            ["uv", "run", script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=work_dir
        )
        output, errors = process.communicate()
        
        # Truncate if output is too large
        size_limit = 10000
        if len(output) >= size_limit:
            return output[:size_limit] + "...truncated due to large size"
        if len(errors) >= size_limit:
            return errors[:size_limit] + "...truncated due to large size"
        
        # Return execution results
        return {
            "stdout": output,
            "stderr": errors,
            "return_code": process.returncode
        }
    except Exception as error:
        return {
            "stdout": "",
            "stderr": str(error),
            "return_code": -1
        }