import sys
import os
import json
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.crawler import DocCrawler
from src.vectara_client import VectaraClient
from src.config import config

async def main():
    # 1. Crawl docs
    crawler = DocCrawler(max_pages=50) # Small batch for testing
    docs = await crawler.crawl()
    
    # 2. Ingest to Vectara
    client = VectaraClient()
    corpus_key = config.CORPUS_KEY
    
    print(f"Ingesting {len(docs)} documents into {corpus_key}...")
    
    with open("crawled_docs.json", "w") as f:
        json.dump(docs, f, indent=2)
        
    for i, doc in enumerate(docs):
        print(f"[{i+1}/{len(docs)}] Ingesting: {doc['title']} ({len(doc['content'])} chars)")
        if len(doc['content']) < 50:
            print(f"Skipping document with too little content: {doc['url']}")
            continue
            
        try:
            client.index_document(
                corpus_key=corpus_key,
                document_id=doc['url'], 
                content=doc['content'],
                metadata=doc['metadata']
            )
            print(f"Successfully ingested: {doc['title']}")
        except Exception as e:
            if "409" in str(e) or "Conflict" in str(e):
                print(f"Document already exists: {doc['title']}")
            else:
                print(f"Error ingesting {doc['url']}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
