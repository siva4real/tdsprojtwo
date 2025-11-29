import os
import csv
import json
from langchain_core.tools import tool


@tool
def read_csv(file_path: str, max_rows: int = 100) -> str:
    """
    Read a CSV file and return its contents as a formatted string.

    This function reads CSV data from disk and returns a structured representation
    of the data including headers and rows. For large files, it limits output to
    prevent overwhelming the conversation context.

    Parameters
    ----------
    file_path : str
        Path to the CSV file relative to LLMFiles directory.
    max_rows : int, optional
        Maximum number of rows to return (default: 100). Set to -1 for all rows.

    Returns
    -------
    str
        JSON string containing headers, data rows, and metadata (total rows, columns).
    """
    try:
        full_path = os.path.join("LLMFiles", file_path)
        
        with open(full_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        if not rows:
            return json.dumps({"error": "CSV file is empty"})
        
        headers = rows[0]
        data_rows = rows[1:]
        total_rows = len(data_rows)
        
        # Limit rows if needed
        if max_rows != -1 and len(data_rows) > max_rows:
            data_rows = data_rows[:max_rows]
            truncated = True
        else:
            truncated = False
        
        result = {
            "headers": headers,
            "data": data_rows,
            "total_rows": total_rows,
            "columns": len(headers),
            "truncated": truncated,
            "rows_returned": len(data_rows)
        }
        
        return json.dumps(result, indent=2)
    except Exception as error:
        return f"Error reading CSV: {error}"


@tool
def write_csv(file_path: str, headers: list[str], rows: list[list[str]]) -> str:
    """
    Write data to a CSV file.

    Creates or overwrites a CSV file with the specified headers and row data.
    The file is saved in the LLMFiles directory.

    Parameters
    ----------
    file_path : str
        Path for the CSV file relative to LLMFiles directory.
    headers : list[str]
        List of column header names.
    rows : list[list[str]]
        List of rows, where each row is a list of values.

    Returns
    -------
    str
        Success message with file path or error message.
    """
    try:
        directory = "LLMFiles"
        os.makedirs(directory, exist_ok=True)
        full_path = os.path.join(directory, file_path)
        
        with open(full_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        
        return f"Successfully wrote {len(rows)} rows to {file_path}"
    except Exception as error:
        return f"Error writing CSV: {error}"


@tool
def csv_to_json(file_path: str) -> str:
    """
    Convert a CSV file to JSON format.

    Reads a CSV file and converts each row into a dictionary using
    the headers as keys, returning a JSON array of objects.

    Parameters
    ----------
    file_path : str
        Path to the CSV file relative to LLMFiles directory.

    Returns
    -------
    str
        JSON string array of row objects or error message.
    """
    try:
        full_path = os.path.join("LLMFiles", file_path)
        
        with open(full_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            data = list(reader)
        
        return json.dumps(data, indent=2)
    except Exception as error:
        return f"Error converting CSV to JSON: {error}"


@tool
def csv_stats(file_path: str) -> str:
    """
    Get statistics about a CSV file.

    Analyzes a CSV file and returns metadata including row count,
    column count, column names, and sample values from each column.

    Parameters
    ----------
    file_path : str
        Path to the CSV file relative to LLMFiles directory.

    Returns
    -------
    str
        JSON string with CSV statistics and metadata.
    """
    try:
        full_path = os.path.join("LLMFiles", file_path)
        
        with open(full_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        if not rows:
            return json.dumps({"error": "CSV file is empty"})
        
        headers = rows[0]
        data_rows = rows[1:]
        
        # Get sample values for each column (first 3 non-empty)
        column_samples = {}
        for i, header in enumerate(headers):
            samples = []
            for row in data_rows:
                if i < len(row) and row[i].strip():
                    samples.append(row[i])
                    if len(samples) >= 3:
                        break
            column_samples[header] = samples
        
        result = {
            "file": file_path,
            "total_rows": len(data_rows),
            "total_columns": len(headers),
            "headers": headers,
            "column_samples": column_samples
        }
        
        return json.dumps(result, indent=2)
    except Exception as error:
        return f"Error analyzing CSV: {error}"

