import os
from langchain_core.tools import tool


@tool
def extract_text_from_pdf(file_path: str, page_numbers: list[int] = None) -> str:
    """
    Extract text content from a PDF file.

    Uses PyMuPDF (fitz) to extract text from PDF pages. Can extract from
    specific pages or the entire document.

    Parameters
    ----------
    file_path : str
        Path to the PDF file relative to LLMFiles directory.
    page_numbers : list[int], optional
        List of page numbers to extract (0-indexed). If None, extracts all pages.

    Returns
    -------
    str
        Extracted text content or error message.
    """
    try:
        import fitz  # PyMuPDF
        
        full_path = os.path.join("LLMFiles", file_path)
        doc = fitz.open(full_path)
        
        text_content = []
        total_pages = len(doc)
        
        if page_numbers is None:
            pages_to_extract = range(total_pages)
        else:
            pages_to_extract = [p for p in page_numbers if 0 <= p < total_pages]
        
        for page_num in pages_to_extract:
            page = doc[page_num]
            text = page.get_text()
            text_content.append(f"--- Page {page_num + 1} ---\n{text}")
        
        doc.close()
        
        result = f"PDF: {file_path} | Total Pages: {total_pages}\n\n"
        result += "\n\n".join(text_content)
        
        return result
    except ImportError:
        return "Error: PyMuPDF (fitz) is required. Install with: pip install pymupdf"
    except Exception as error:
        return f"Error extracting PDF text: {error}"


@tool
def get_pdf_info(file_path: str) -> str:
    """
    Get metadata and information about a PDF file.

    Extracts PDF metadata including page count, title, author, 
    creation date, and page dimensions.

    Parameters
    ----------
    file_path : str
        Path to the PDF file relative to LLMFiles directory.

    Returns
    -------
    str
        JSON string with PDF metadata or error message.
    """
    try:
        import fitz  # PyMuPDF
        import json
        
        full_path = os.path.join("LLMFiles", file_path)
        doc = fitz.open(full_path)
        
        metadata = doc.metadata
        
        # Get page dimensions from first page
        first_page = doc[0] if len(doc) > 0 else None
        page_size = None
        if first_page:
            rect = first_page.rect
            page_size = {
                "width": rect.width,
                "height": rect.height
            }
        
        info = {
            "file": file_path,
            "page_count": len(doc),
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creation_date": metadata.get("creationDate", ""),
            "modification_date": metadata.get("modDate", ""),
            "page_size": page_size
        }
        
        doc.close()
        
        return json.dumps(info, indent=2)
    except ImportError:
        return "Error: PyMuPDF (fitz) is required. Install with: pip install pymupdf"
    except Exception as error:
        return f"Error getting PDF info: {error}"


@tool
def extract_pdf_tables(file_path: str, page_number: int = 0) -> str:
    """
    Extract tables from a specific page of a PDF file.

    Uses PyMuPDF to detect and extract tabular data from PDF pages.
    Returns tables as JSON arrays.

    Parameters
    ----------
    file_path : str
        Path to the PDF file relative to LLMFiles directory.
    page_number : int, optional
        Page number to extract tables from (0-indexed, default: 0).

    Returns
    -------
    str
        JSON string with extracted tables or error message.
    """
    try:
        import fitz  # PyMuPDF
        import json
        
        full_path = os.path.join("LLMFiles", file_path)
        doc = fitz.open(full_path)
        
        if page_number < 0 or page_number >= len(doc):
            doc.close()
            return f"Error: Page {page_number} does not exist. PDF has {len(doc)} pages."
        
        page = doc[page_number]
        tables = page.find_tables()
        
        extracted_tables = []
        for i, table in enumerate(tables):
            table_data = table.extract()
            extracted_tables.append({
                "table_index": i,
                "rows": len(table_data),
                "cols": len(table_data[0]) if table_data else 0,
                "data": table_data
            })
        
        doc.close()
        
        result = {
            "file": file_path,
            "page": page_number,
            "tables_found": len(extracted_tables),
            "tables": extracted_tables
        }
        
        return json.dumps(result, indent=2)
    except ImportError:
        return "Error: PyMuPDF (fitz) is required. Install with: pip install pymupdf"
    except Exception as error:
        return f"Error extracting PDF tables: {error}"


@tool
def pdf_to_images(file_path: str, page_numbers: list[int] = None, dpi: int = 150) -> str:
    """
    Convert PDF pages to images.

    Renders PDF pages as PNG images and saves them to the LLMFiles directory.
    Useful for OCR processing or visual inspection.

    Parameters
    ----------
    file_path : str
        Path to the PDF file relative to LLMFiles directory.
    page_numbers : list[int], optional
        List of page numbers to convert (0-indexed). If None, converts all pages.
    dpi : int, optional
        Resolution for rendered images (default: 150).

    Returns
    -------
    str
        List of generated image filenames or error message.
    """
    try:
        import fitz  # PyMuPDF
        import json
        
        full_path = os.path.join("LLMFiles", file_path)
        doc = fitz.open(full_path)
        
        total_pages = len(doc)
        base_name = os.path.splitext(file_path)[0]
        
        if page_numbers is None:
            pages_to_convert = range(total_pages)
        else:
            pages_to_convert = [p for p in page_numbers if 0 <= p < total_pages]
        
        generated_files = []
        zoom = dpi / 72  # PDF default is 72 DPI
        matrix = fitz.Matrix(zoom, zoom)
        
        for page_num in pages_to_convert:
            page = doc[page_num]
            pix = page.get_pixmap(matrix=matrix)
            
            image_filename = f"{base_name}_page_{page_num + 1}.png"
            image_path = os.path.join("LLMFiles", image_filename)
            pix.save(image_path)
            generated_files.append(image_filename)
        
        doc.close()
        
        result = {
            "source_pdf": file_path,
            "pages_converted": len(generated_files),
            "dpi": dpi,
            "generated_images": generated_files
        }
        
        return json.dumps(result, indent=2)
    except ImportError:
        return "Error: PyMuPDF (fitz) is required. Install with: pip install pymupdf"
    except Exception as error:
        return f"Error converting PDF to images: {error}"

