import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vectara_client import VectaraClient
from src.config import config
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

def main():
    console = Console()
    client = VectaraClient()
    
    agent_key = os.getenv("VECTARA_AGENT_KEY")
    query = "How do I create a corpus with specific filter attributes, then upload a PDF, and finally query it with a metadata filter for doc.section='rest-api'? Please combine all these steps."
    
    console.print(f"[bold]Querying Native Agent:[/bold] {query}")
    
    try:
        session = client.create_session(agent_key)
        console.print(f"Session Response: {session}")
        session_id = session.get('key') or session.get('id')
        response = client.chat(agent_key, session_id, query)
        console.print(f"Chat Response: {json.dumps(response, indent=2)}")
        
        events = response.get('events', [])
        final_answer = ""
        thinking_steps = []
        
        for event in events:
            if event['type'] == 'agent_output':
                final_answer = event['content']
            elif event['type'] == 'message' and event['role'] == 'assistant':
                final_answer = event['content']
            elif event['type'] == 'tool_call':
                tool_name = event.get('tool_name', 'tool')
                tool_input = event.get('input', {})
                thinking_steps.append(f"  - **Tool Call** [cyan]{tool_name}[/cyan]: {json.dumps(tool_input)}")
            elif event['type'] == 'tool_output':
                tool_name = event.get('tool_name', 'tool')
                thinking_steps.append(f"  - **Tool Output** from {tool_name}")
        
        if thinking_steps:
            console.print("\n[bold blue]Tool Usage Log:[/bold blue]")
            for step in thinking_steps:
                console.print(Markdown(step))
                
        console.print("\n[bold blue]Final Agent Answer:[/bold blue]")
        console.print(Panel(Markdown(final_answer or "No response."), title="Agent Response"))
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if hasattr(e, 'response') and e.response is not None:
            console.print(f"Response: {e.response.text}")

if __name__ == "__main__":
    main()
