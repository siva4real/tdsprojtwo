import os
import base64
import uuid
from langchain_core.tools import tool
from shared_store import BASE64_STORE

@tool
def encode_image_to_base64(image_path: str) -> str:
    """
    Converts an image file to Base64 encoding and returns a reference key.

    This function reads image data from disk, encodes it to Base64, and stores
    the encoded string in a shared memory cache. Rather than exposing the complete
    Base64 output (which can be large and overwhelm the conversation context), 
    it returns a compact reference key in the format:

        BASE64_KEY:<unique-identifier>

    The reference key can be used by downstream tools (like post_request) which
    will substitute the actual Base64 string when needed.

    Benefits:
    - Prevents excessive token usage in conversation history
    - Avoids malformed tool call issues caused by large string outputs
    - Reduces memory overhead and improves response handling
    - Maintains clean separation between encoding and transmission

    Parameters
    ----------
    image_path : str
        Path to the image file (PNG, JPG, GIF, WEBP, etc.)

    Returns
    -------
    str
        Reference key in format "BASE64_KEY:<uuid>" or error message
    """
    try:
        # Construct full path within working directory
        full_path = os.path.join("LLMFiles", image_path)
        
        # Read binary image data
        with open(full_path, "rb") as image_file:
            binary_data = image_file.read()
    
        # Encode to Base64 string
        base64_string = base64.b64encode(binary_data).decode("utf-8")

        # Generate unique identifier and store in cache
        unique_key = str(uuid.uuid4())
        BASE64_STORE[unique_key] = base64_string

        return f"BASE64_KEY:{unique_key}"
    except Exception as error:
        return f"Error occurred: {error}"