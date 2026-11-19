"""Master runner for NoSQL Lab 5: Aggregation Pipeline & $lookup Joins
Author: K. Pranav Reddy (24BTRCL098)
"""

import sys
import subprocess
from rich.console import Console
from rich.panel import Panel

console = Console()


def run_script(script_name: str):
    console.print(Panel(f"[bold cyan]Executing: {script_name}[/bold cyan]", expand=False))
    result = subprocess.run([sys.executable, script_name], capture_output=False)
    if result.returncode != 0:
        console.print(f"[bold red]Execution of {script_name} failed with code {result.returncode}[/bold red]")
        sys.exit(result.returncode)
    console.print(f"[bold green]✔ Successfully completed {script_name}[/bold green]\n")


def main():
    console.print(Panel.fit(
        "[bold green]NoSQL Database Engineering - Lab 5 Test Harness[/bold green]\n"
        "[white]Student: K. Pranav Reddy (24BTRCL098)[/white]\n"
        "[yellow]Topics: Aggregation Pipelines, $group, $sort, $bucket, $switch, $lookup, $unwind[/yellow]",
        border_style="blue"
    ))

    run_script("lab_01_sales_analytics.py")
    run_script("lab_02_lookup_joins.py")

    console.print(Panel.fit(
        "[bold green]ALL LAB 5 ACTIVITIES COMPLETED SUCCESSFULLY![/bold green]",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
