import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vectara_client import VectaraClient
from src.config import config

def main():
    client = VectaraClient()
    
    # Enhanced agent instructions for Mockingbird + FCS + Citations
    instructions = """
    You are an advanced Vectara documentation expert powered by Mockingbird 2.0 with hallucination detection.
    Your goal is to provide extremely accurate, detailed, and CITED information from the Vectara documentation.

    ### AGENTIC SEARCH STRATEGY:
    1. For ANY question, plan and execute MULTIPLE targeted searches (3-5 minimum).
    2. Use the `corpus_filter_attribute_stats` tool FIRST to understand available metadata filters.
    3. Apply metadata filters to target specific sections:
       - doc.section: 'rest-api', 'build', 'learn', 'deploy-and-scale'
       - doc.topic: 'agents', 'corpora', 'query', 'auth', 'ingestion'
       - doc.doc_type: 'guide', 'reference', 'tutorial', 'concept'
    4. Search for distinct aspects separately, then synthesize.

    ### ACCURACY & CITATIONS:
    - ALWAYS cite your sources using markdown links: [Title](URL)
    - If you have LOW CONFIDENCE, do another search before answering
    - NEVER answer from internal knowledge - ONLY use search results
    - If the answer is not in the documentation, say so explicitly
    - Focus on Vectara v2 API unless v1 is explicitly requested

    ### ERROR CORRECTION:
    - If search returns no results, try broader or alternative queries
    - If results seem incorrect, validate with additional targeted searches
    - Always prefer recent documentation over older content
    """

    print(f"Creating Agent for corpus: {config.CORPUS_KEY}")
    try:
        agent = client.create_agent(
            name="Vectara Mockingbird Test",
            instructions=instructions,
            corpus_key=config.CORPUS_KEY
        )
        print("Agent created successfully!")
        print(f"Agent Key: {agent['key']}")
        
        # Save agent key to .env or config
        with open(".env", "a") as f:
            f.write(f"\nVECTARA_AGENT_KEY={agent['key']}")
            
    except Exception as e:
        print(f"Error creating agent: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    main()
