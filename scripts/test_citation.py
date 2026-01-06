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
        
        # Save full response
        with open("test_citation_response.json", "w") as f:
            json.dump(response, f, indent=2)
        print("Full response saved to test_citation_response.json\n")
        
        # Extract and analyze all events
        events = response.get('events', [])
        
        print("="*80)
        print("ANALYZING ALL EVENTS:")
        print("="*80)
        
        for i, event in enumerate(events):
            print(f"\n--- Event {i+1}: {event['type']} ---")
            
            if event['type'] == 'tool_output':
                tool_name = event.get('tool_configuration_name', 'unknown')
                tool_output = event.get('tool_output', {})
                
                # Check for summary/citations in tool output
                if 'summary' in tool_output:
                    print(f"  Tool: {tool_name}")
                    print(f"  Summary: {tool_output['summary'][:200]}...")
                    
                if 'factual_consistency_score' in tool_output:
                    print(f"  FCS Score: {tool_output['factual_consistency_score']}")
                    
                if 'search_results' in tool_output:
                    print(f"  Search Results Count: {len(tool_output['search_results'])}")
                    
                if 'error' in tool_output:
                    print(f"  ERROR: {tool_output['error']}")
                    
            elif event['type'] == 'agent_output':
                answer = event['content']
                print(f"\n  AGENT OUTPUT:")
                print(f"  {answer}")
                
                # Check for citations
                has_markdown_links = '[' in answer and '](' in answer and ')' in answer
                has_reference_abc = "Reference: abc" in answer
                
                print(f"\n  ✓ Has markdown links: {has_markdown_links}")
                print(f"  ✓ Has 'Reference: abc': {has_reference_abc}")
                
                if has_markdown_links:
                    # Extract all markdown links
                    import re
                    links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', answer)
                    print(f"\n  Found {len(links)} citation(s):")
                    for title, url in links:
                        print(f"    - [{title}]({url})")
        
        print("\n" + "="*80)
        print("FINAL VERDICT:")
        print("="*80)
        
        # Find final answer
        final_answer = None
        for event in events:
            if event['type'] == 'agent_output':
                final_answer = event['content']
                
        if final_answer:
            has_citations = '[' in final_answer and '](' in final_answer
            has_ref_abc = "Reference: abc" in final_answer
            
            if has_citations and has_ref_abc:
                print("✅ SUCCESS! Both citations AND 'Reference: abc' found!")
                print("   Generation model with custom prompt is FULLY WORKING!")
            elif has_ref_abc:
                print("⚠️  PARTIAL: 'Reference: abc' found but NO citations")
                print("   Custom prompt works, but citations may not be enabled")
            elif has_citations:
                print("⚠️  PARTIAL: Citations found but NO 'Reference: abc'")
                print("   Citations work, but custom prompt may not be applied")
            else:
                print("❌ FAILED: Neither citations nor 'Reference: abc' found")
                print("   Generation model may not be working correctly")
        else:
            print("❌ ERROR: No agent output found in response")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
