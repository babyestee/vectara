import sys
import os
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vectara_client import VectaraClient
from src.config import config

def main():
    client = VectaraClient()
    print(f"Creating corpus: {config.CORPUS_KEY}...")
    try:
        response = client.create_corpus(
            name="Vectara Documentation RAG",
            key=config.CORPUS_KEY,
            description="Complete documentation for Vectara platform"
        )
        print("Corpus created successfully!")
        print(response)
    except requests.exceptions.HTTPError as e:
        print(f"Error creating corpus: {e}")
        if e.response is not None:
            print(f"Response content: {e.response.text}")
        if "409" in str(e) or "Conflict" in str(e):
             print("Corpus already exists. Continuing...")
        else:
            sys.exit(1)
    except Exception as e:
        print(f"General error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
