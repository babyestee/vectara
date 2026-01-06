import sys
import os
import json
import time
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
    if not agent_key:
        console.print("[red]Error: VECTARA_AGENT_KEY not found in .env. Run scripts/init_agent.py first.[/red]")
        return
        
    console.print(Panel(
        f"[bold blue]Vectara Native Agent Demo[/bold blue]\n"
        f"Agent: {agent_key}\n"
        f"[yellow][dim]Note: For full FCS + Mockingbird 2.0, use demo.py instead[/dim][/yellow]"
    ))
    
    # Create a session
    try:
        session = client.create_session(agent_key)
        session_id = session.get('key') or session.get('id')
        console.print(f"[dim]Session created: {session_id}[/dim]")
    except Exception as e:
        console.print(f"[red]Failed to create session: {e}[/red]")
        return

    while True:
        user_input = console.input("\n[bold green]Ask the Vectara Agent (or 'exit'): [/bold green]")
        if user_input.lower() in ['exit', 'quit', 'q']:
            break
            
        with console.status("[bold yellow]Agent is processing and calling tools...[/bold yellow]"):
            try:
                response = client.chat(agent_key, session_id, user_input)
                
                events = response.get('events', [])
                final_answer = ""
                thinking_steps = []
                
                for event in events:
                    if event['type'] == 'agent_output':
                        final_answer = event['content']
                    elif event['type'] == 'message' and event.get('role') == 'assistant':
                        final_answer = event['content']
                    elif event['type'] == 'tool_call':
                        tool_name = event.get('tool_name', 'tool')
                        query = event.get('input', {}).get('query', '')
                        thinking_steps.append(f"  - Tool Call: [cyan]{tool_name}[/cyan] ({query})")
                    elif event['type'] == 'tool_output':
                        tool_name = event.get('tool_name', 'tool')
                        thinking_steps.append(f"  - Tool Output from: [dim]{tool_name}[/dim]")
                
                if thinking_steps:
                    console.print("\n[bold blue]Agent Thinking & Tool Usage:[/bold blue]")
                    for step in thinking_steps:
                        console.print(step)
                        
                console.print("\n[bold blue]Agent Answer:[/bold blue]")
                console.print(Panel(Markdown(final_answer or "No response from agent."), title="Vectara Agent Response"))
                
            except Exception as e:
                console.print(f"[red]Error during chat: {e}[/red]")
                if hasattr(e, 'response') and e.response is not None:
                    console.print(f"[dim]Response: {e.response.text}[/dim]")

if __name__ == "__main__":
    main()
