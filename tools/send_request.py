import time
import os
import json
from collections import defaultdict
from typing import Any, Dict, Optional
import requests
from langchain_core.tools import tool
from shared_store import BASE64_STORE, url_time

# Track request attempts per URL
request_counter = defaultdict(int)
MAX_RETRY_ATTEMPTS = 4

@tool
def post_request(url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Any:
    """
    Submits an HTTP POST request with JSON payload to a specified endpoint.

    This tool is designed for LangGraph agent workflows, enabling communication
    with external APIs, webhooks, or backend services. It handles Base64 key
    substitution and implements retry logic based on response correctness.
    
    NOTE: This is a blocking operation that waits for server response.

    Args:
        url (str): Target endpoint URL
        payload (Dict[str, Any]): JSON-compatible request body
        headers (Optional[Dict[str, str]]): HTTP headers (defaults to JSON content type)

    Returns:
        Any: Parsed JSON response or raw text if JSON parsing fails

    Raises:
        requests.HTTPError: On 4xx/5xx HTTP status codes
        requests.RequestException: On network-related failures
    """
    # Substitute Base64 reference with actual encoded data
    answer_value = payload.get("answer")

    if isinstance(answer_value, str) and answer_value.startswith("BASE64_KEY:"):
        reference_key = answer_value.split(":", 1)[1]
        payload["answer"] = BASE64_STORE[reference_key]
    
    # Set default headers if not provided
    headers = headers or {"Content-Type": "application/json"}
    
    try:
        active_url = os.getenv("url")
        request_counter[active_url] += 1
        
        # Create truncated version for logging
        log_payload = payload
        if isinstance(payload.get("answer"), str):
            log_payload = {
                "answer": payload.get("answer", "")[:100],
                "email": payload.get("email", ""),
                "url": payload.get("url", "")
            }
        print(f"\nSending Answer \n{json.dumps(log_payload, indent=4)}\n to url: {url}")
        
        # Execute HTTP POST request
        response = requests.post(url, json=payload, headers=headers)

        # Validate response status
        response.raise_for_status()

        # Parse response data
        response_data = response.json()
        print("Got the response: \n", json.dumps(response_data, indent=4), '\n')
        
        # Calculate time elapsed for current URL
        elapsed_time = time.time() - url_time.get(active_url, time.time())
        print(elapsed_time)
        
        next_url = response_data.get("url") 
        if not next_url:
            return "Tasks completed"
        
        # Track timing for new URL
        if next_url not in url_time:
            url_time[next_url] = time.time()

        is_correct = response_data.get("correct")
        if not is_correct:
            current_time = time.time()
            previous_time = url_time.get(next_url, time.time())
            
            # Determine if retry should be skipped
            should_skip = (request_counter[active_url] >= MAX_RETRY_ATTEMPTS or 
                          elapsed_time >= 180 or 
                          (previous_time != "0" and (current_time - float(previous_time)) > 90))
            
            if should_skip:
                print("Not retrying, moving on to the next question")
                response_data = {"url": response_data.get("url", "")} 
            else:  # Perform retry
                os.environ["offset"] = str(url_time.get(next_url, time.time()))
                print("Retrying..")
                response_data["url"] = active_url
                response_data["message"] = "Retry Again!" 
        
        print("Formatted: \n", json.dumps(response_data, indent=4), '\n')
        
        # Update environment with next URL
        target_url = response_data.get("url", "")
        os.environ["url"] = target_url 
        if target_url == next_url:
            os.environ["offset"] = "0"

        return response_data
    except requests.HTTPError as http_error:
        # Extract error details from response
        error_response = http_error.response

        try:
            error_data = error_response.json()
        except ValueError:
            error_data = error_response.text

        print("HTTP Error Response:\n", error_data)
        return error_data

    except Exception as general_error:
        print("Unexpected error:", general_error)
        return str(general_error)