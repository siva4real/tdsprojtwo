import os
import base64
from io import BytesIO
from PIL import Image
import pytesseract


def load_image(image_input):
    """
    Loads an image from various input formats.
    
    Supports: raw bytes, PIL Image object, Base64 data URL, or file path.
    """
    if isinstance(image_input, bytes):
        # Convert raw bytes to PIL Image
        return Image.open(BytesIO(image_input)).convert("RGB")
    
    if isinstance(image_input, Image.Image):
        # Already a PIL Image, just ensure RGB format
        return image_input.convert("RGB")
    
    if isinstance(image_input, str):
        # Check if it's a Base64 data URL
        if image_input.startswith("data:"):
            _, encoded_data = image_input.split(",", 1)
            decoded_bytes = base64.b64decode(encoded_data)
            return Image.open(BytesIO(decoded_bytes)).convert("RGB")
        
        # Treat as file path
        file_path = os.path.join("LLMFiles", image_input)
        return Image.open(file_path).convert("RGB")
    
    raise ValueError("Unsupported image input type")


def ocr_image_tool(payload: dict) -> dict:
    """
    Performs optical character recognition (OCR) on an image using pytesseract.

    Payload structure:
    {
        "image": bytes | base64 string | file path | PIL.Image object,
        "lang": "eng" (optional, defaults to English)
    }

    Returns:
    {
        "text": "<extracted text content>",
        "engine": "pytesseract"
    }

    Used to extract readable text from images containing written content.
    """
    try:
        image_source = payload["image"]
        language_code = payload.get("lang", "eng")

        # Load and process image
        image_object = load_image(image_source)
        extracted_text = pytesseract.image_to_string(image_object, lang=language_code)

        return {
            "text": extracted_text.strip(),
            "engine": "pytesseract"
        }
    except Exception as error:
        return f"Error occurred: {error}"
