from rich.console import Console
from rich.prompt import Prompt
from nltaskgraph import go

def tui():
    c = Console()
    c.print("[bold]NL Task Agent[/bold]\n")
    while (task := Prompt.ask("[green]>[/green]")) not in ("q", "quit", "exit"): go(task)

if __name__ == "__main__": tui()