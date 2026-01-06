import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vectara_client import VectaraClient
from src.config import config

def main():
    client = VectaraClient()
    
    agent_key = os.getenv("VECTARA_AGENT_KEY")
    
    # Simple short query to avoid context limits
    query = "What is Vectara?"
    
    print(f"Testing with simple query: {query}")
    print(f"Agent key: {agent_key}\n")
    
    try:
        session = client.create_session(agent_key)
        session_id = session.get('key') or session.get('id')
        response = client.chat(agent_key, session_id, query)
        
        # Extract final answer
        events = response.get('events', [])
        for event in events:
            if event['type'] == 'agent_output':
                answer = event['content']
                print("="*80)
                print("FINAL ANSWER:")
                print("="*80)
                print(answer)
                print("="*80)
                
                # Check for "Reference: abc"
                if "Reference: abc" in answer:
                    print("\n✅ SUCCESS! Found 'Reference: abc' in response")
                    print("Generation model custom prompt is working!")
                else:
                    print("\n❌ FAILED! 'Reference: abc' NOT found in response")
                    print("Generation model custom prompt is NOT working")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
