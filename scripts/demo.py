import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vectara_client import VectaraClient
from src.query_planner import QueryOrchestrator
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

def main():
    console = Console()
    client = VectaraClient()
    orchestrator = QueryOrchestrator(client)
    
    console.print(Panel(
        "[bold blue]Vectara Advanced Agentic RAG Demo[/bold blue]\n"
        "[dim]Features: Multi-Query Planning | Mockingbird 2.0 | FCS | Citations[/dim]"
    ))
    
    while True:
        user_input = console.input("\n[bold green]Ask a question about Vectara (or 'exit'): [/bold green]")
        if user_input.lower() in ['exit', 'quit', 'q']:
            break
            
        with console.status("[bold yellow]Agent is planning and executing searches...[/bold yellow]"):
            result = orchestrator.execute_agentic_rag(user_input)
        
        # Display executed plan
        console.print("\n[bold blue]📋 Query Plan Executed:[/bold blue]")
        plan_table = Table(show_header=True, header_style="bold cyan")
        plan_table.add_column("#", width=3)
        plan_table.add_column("Query", width=40)
        plan_table.add_column("Filter", width=30)
        plan_table.add_column("Reason", width=30)
        
        for i, step in enumerate(result['plan']):
            plan_table.add_row(
                str(i+1), 
                step['query'], 
                step['filter'] or "[dim]none[/dim]",
                step['reason']
            )
        console.print(plan_table)
        
        # Display stats
        console.print(f"\n[dim]📊 Gathered {result.get('search_results_count', 'N/A')} unique document segments[/dim]")
        
        # Display answer
        console.print("\n[bold blue]🤖 Agent Answer (Mockingbird 2.0):[/bold blue]")
        console.print(Panel(Markdown(result['answer']), title="Final Response with Citations"))
        
        # Display FCS score with color coding
        fcs = result.get('fcs', 0)
        if fcs > 0:
            if fcs >= 0.8:
                color = "green"
                status = "High Confidence"
            elif fcs >= 0.5:
                color = "yellow"
                status = "Medium Confidence"
            else:
                color = "red"
                status = "Low Confidence - May contain hallucinations"
            console.print(f"\n[bold {color}]🎯 Factual Consistency Score (FCS): {fcs:.2f} - {status}[/bold {color}]")
        else:
            console.print("\n[dim]🎯 FCS: Not available for this response[/dim]")
        
        # Display citations if available
        citations = result.get('citations', [])
        if citations:
            console.print("\n[bold blue]📚 Citations:[/bold blue]")
            for i, cite in enumerate(citations):
                console.print(f"  [{i+1}] {cite}")

if __name__ == "__main__":
    main()
