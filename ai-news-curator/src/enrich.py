import re
import requests
import trafilatura
import xml.etree.ElementTree as ET
from typing import List, Optional
from urllib.parse import urlparse

from src.models import EnrichedLink

def extract_links(text: str) -> List[str]:
    """Extracts all URLs from a given text."""
    return re.findall(r"https?://\S+", text)

def classify_link(url: str) -> str:
    """Classifies a link based on its domain."""
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc
    path = parsed_url.path

    if 'github.com' in netloc and len(path.strip('/').split('/')) >= 2:
        return "github"
    if 'arxiv.org' in netloc:
        return "arxiv"
    # Add more specific classifiers if needed
    return "article"

def enrich_github(url: str, token: Optional[str]) -> EnrichedLink:
    """Enriches a GitHub link by fetching the README."""
    parsed_url = urlparse(url)
    parts = parsed_url.path.strip('/').split('/')
    owner, repo = parts[0], parts[1]
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    headers = {"Accept": "application/vnd.github.raw+json"}
    if token:
        headers["Authorization"] = f"token {token}"
        
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return EnrichedLink(url=url, source_type="github", title=f"{owner}/{repo}", content=response.text, fetch_error=None)
    except requests.RequestException as e:
        return EnrichedLink(url=url, source_type="github", title=f"{owner}/{repo}", content=None, fetch_error=str(e))

def enrich_arxiv(url: str) -> EnrichedLink:
    """Enriches an arXiv link by fetching the abstract."""
    arxiv_id = url.split('/')[-1]
    api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entry = root.find('atom:entry', ns)
        
        if entry:
            title = entry.find('atom:title', ns).text.strip()
            abstract = entry.find('atom:summary', ns).text.strip()
            return EnrichedLink(url=url, source_type="arxiv", title=title, content=abstract, fetch_error=None)
        else:
            return EnrichedLink(url=url, source_type="arxiv", title=None, content=None, fetch_error="ArXiv entry not found in API response.")
            
    except (requests.RequestException, ET.ParseError) as e:
        return EnrichedLink(url=url, source_type="arxiv", title=None, content=None, fetch_error=str(e))

def enrich_article(url: str) -> EnrichedLink:
    """Enriches a generic article link using trafilatura."""
    try:
        # Add a user-agent to look more like a browser
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        downloaded = response.text
        
        content = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        
        if content:
            title_match = re.search(r'<title>(.*?)</title>', downloaded, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else None
            return EnrichedLink(url=url, source_type="article", title=title, content=content, fetch_error=None)
        else:
            return EnrichedLink(url=url, source_type="article", title=None, content=None, fetch_error="Trafilatura could not extract main content.")

    except requests.RequestException as e:
        return EnrichedLink(url=url, source_type="article", title=None, content=None, fetch_error=f"Failed to fetch URL: {e}")

def enrich_link(url: str, github_token: Optional[str] = None) -> EnrichedLink:
    """Dispatches URL to the correct enrichment function."""
    link_type = classify_link(url)
    
    try:
        if link_type == "github":
            return enrich_github(url, github_token)
        elif link_type == "arxiv":
            return enrich_arxiv(url)
        elif link_type == "article":
            return enrich_article(url)
        else: # "unknown"
            return EnrichedLink(url=url, source_type="unknown", title=None, content=None, fetch_error="Unknown link type.")
    except Exception as e:
        return EnrichedLink(url=url, source_type=link_type, title=None, content=None, fetch_error=f"An unexpected error occurred: {e}")


if __name__ == '__main__':
    # Test URLs
    test_urls = {
        "github": "https://github.com/jdepoix/youtube-transcript-api",
        "arxiv": "https://arxiv.org/abs/2303.08774", # "Sparks of AGI" paper
        "article": "https://en.wikipedia.org/wiki/Artificial_intelligence"
    }

    print("--- Testing enrich.py ---")

    for link_type, url in test_urls.items():
        print(f"\n--- Enriching {link_type.upper()} link: {url} ---")
        enriched_link = enrich_link(url) # No GitHub token for this test
        
        if enriched_link and not enriched_link.fetch_error:
            print(f"   ✅ Success! Type: {enriched_link.source_type}")
            print(f"   Title: {enriched_link.title}")
            print(f"   Content (first 100 chars): '{enriched_link.content[:100].strip()}...'")
        elif enriched_link:
            print(f"   ❌ Failed to enrich link. Error: {enriched_link.fetch_error}")
        else:
            print("   ❌ Enrichment returned None.")
            
    print("\n--- Test complete ---")
