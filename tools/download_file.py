import os
import requests
from langchain_core.tools import tool

@tool
def download_file(url: str, filename: str) -> str:
    """
    Downloads a file from a remote URL and saves it to local storage.

    The file is saved in a designated directory (LLMFiles) with the specified
    filename. The download is performed in streaming mode to handle large files
    efficiently without loading the entire content into memory.

    Args:
        url (str): Remote URL pointing to the file to download
        filename (str): Desired name for the saved file

    Returns:
        str: Name of the saved file on success, or error message on failure
    """
    try:
        # Stream download from URL
        http_response = requests.get(url, stream=True)
        http_response.raise_for_status()
        
        # Ensure target directory exists
        target_dir = "LLMFiles"
        os.makedirs(target_dir, exist_ok=True)
        
        # Construct full file path
        file_path = os.path.join(target_dir, filename)
        
        # Write file in chunks
        with open(file_path, "wb") as output_file:
            for data_chunk in http_response.iter_content(chunk_size=8192):
                if data_chunk:
                    output_file.write(data_chunk)

        return filename
    except Exception as error:
        return f"Error downloading file: {str(error)}"