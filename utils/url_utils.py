from typing import List
from urllib.parse import urlparse, urlunparse


def clean_url(url: str) -> str:
    """Clean and normalize a URL, ensuring it includes a protocol."""
    url = url.strip()
    
    # Parse the URL using urllib
    parsed_url = urlparse(url)

    # If no scheme is provided, default to https
    scheme = parsed_url.scheme or "https"
    
    # Handle missing 'www' in the netloc (domain)
    # netloc = parsed_url.netloc or parsed_url.path.split('/')[0]
    # if not netloc.startswith("www.") and "." in netloc:
    #     netloc = "www." + netloc
    
    # Rebuild the URL, preserving the query parameters
    path = parsed_url.path if parsed_url.netloc else "/" + "/".join(parsed_url.path.split('/')[1:])
    query = parsed_url.query  # Preserve the query string
    cleaned_url = urlunparse(
        (
            scheme,
            # netloc,
            parsed_url.netloc,
            path,
            '',
            query,
            ''
        )
    )
    
    return cleaned_url

def extract_and_clean_urls(input_str: str) -> List[str]:
    """Extract, clean, and normalize all URLs from a given input string."""
    urls = input_str.replace(',', ' ').split()
    return list(map(clean_url, urls))
