import asyncio
from crawl4ai import AsyncWebCrawler
from urllib.parse import urljoin, urlparse
import json

class DocCrawler:
    def __init__(self, base_url="https://docs.vectara.com", max_pages=150):
        self.base_url = base_url
        self.max_pages = max_pages
        self.docs = []
        self.visited = set()

    async def crawl(self):
        print(f"Starting async crawl using crawl4ai of {self.base_url}...")
        
        async with AsyncWebCrawler() as crawler:
            to_visit = [self.base_url]
            
            while to_visit and len(self.visited) < self.max_pages:
                url = to_visit.pop(0)
                if url in self.visited:
                    continue
                
                print(f"Crawling: {url}")
                result = await crawler.arun(url=url)
                
                if result.success:
                    self.visited.add(url)
                    
                    # crawl4ai result provides markdown directly often
                    content = result.markdown
                    title = result.metadata.get('title', url)
                    
                    self.docs.append({
                        "url": url,
                        "title": title,
                        "content": content,
                        "metadata": self.extract_metadata(url, title)
                    })
                    
                    # Extract internal links from common locations
                    # Note: crawl4ai might already provide links in newer versions
                    # For now, let's assume we need to find them or use result.links
                    # If result.links exists, use it
                    if hasattr(result, 'links') and result.links:
                        for link_obj in result.links.get('internal', []):
                            # In newer crawl4ai, link_obj is a dict with 'href' key
                            link = link_obj.get('href', '') if isinstance(link_obj, dict) else link_obj
                            if not link: continue
                            
                            clean_link = link.split('#')[0]
                            if clean_link.startswith(self.base_url) and clean_link not in self.visited:
                                to_visit.append(clean_link)
                    else:
                        # Fallback: crawl4ai usually handles complex extraction
                        pass
                else:
                    print(f"Failed to crawl {url}: {result.error_message}")
                
            print(f"Finished crawling. Found {len(self.docs)} documents.")
            return self.docs

    def extract_metadata(self, url, title):
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        section = "general"
        topic = "general"
        doc_type = "guide"
        
        if len(path_parts) >= 1:
            section = path_parts[0]
        if len(path_parts) >= 2:
            topic = path_parts[1]
            
        if "api-reference" in path_parts or "rest-api" in path_parts:
            doc_type = "reference"
        elif "tutorial" in path_parts:
            doc_type = "tutorial"
        elif "concept" in path_parts:
            doc_type = "concept"
            
        return {
            "section": section,
            "topic": topic,
            "doc_type": doc_type,
            "url": url,
            "title": title
        }
