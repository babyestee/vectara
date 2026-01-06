import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_KEY = os.getenv("VECTARA_API_KEY")
    CORPUS_KEY = os.getenv("VECTARA_CORPUS_KEY", "vectara-docs-rag")
    API_URL = os.getenv("VECTARA_API_URL", "https://api.vectara.io/v2/")
    
    # Metadata filters configuration
    FILTER_ATTRIBUTES = [
        {"name": "section", "level": "document", "type": "text", "indexed": True},
        {"name": "topic", "level": "document", "type": "text", "indexed": True},
        {"name": "doc_type", "level": "document", "type": "text", "indexed": True},
        {"name": "url", "level": "document", "type": "text", "indexed": False},
        {"name": "title", "level": "document", "type": "text", "indexed": False},
    ]

config = Config()
