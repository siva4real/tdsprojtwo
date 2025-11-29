from urllib.parse import urljoin
from langchain_core.tools import tool
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

@tool
def get_rendered_html(url: str) -> dict:
    """
    Retrieves fully rendered HTML content from a webpage using headless browser.
    
    This function launches a headless Chromium browser, navigates to the specified
    URL, waits for network idle state, and extracts the rendered HTML along with
    all image URLs found on the page.
    """
    print("\nFetching and rendering:", url)
    try:
        with sync_playwright() as playwright:
            # Launch headless browser
            browser_instance = playwright.chromium.launch(headless=True)
            webpage = browser_instance.new_page()

            # Navigate and wait for page to fully load
            webpage.goto(url, wait_until="networkidle")
            html_content = webpage.content()

            browser_instance.close()

            # Extract image URLs from HTML
            parser = BeautifulSoup(html_content, "html.parser")
            image_urls = [urljoin(url, image["src"]) for image in parser.find_all("img", src=True)]
            
            # Truncate if content exceeds size limit
            if len(html_content) > 300000:
                print("Warning: HTML too large, truncating...")
                html_content = html_content[:300000] + "... [TRUNCATED DUE TO SIZE]"
            
            return {
                "html": html_content,
                "images": image_urls,
                "url": url
            }

    except Exception as error:
        return {"error": f"Error fetching/rendering page: {str(error)}"}


