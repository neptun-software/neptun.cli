import typer
from neptun.utils.services import ApplicationService
from neptun.model.http_responses import HealthCheckResponse
from rich.console import Console

health_app = typer.Typer(name="Health-Checker", help="You can use health to check the status of the NEPTUN-API.")
console = Console()


@health_app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        application_service = ApplicationService()
        health_status = application_service.check_health()

        if isinstance(health_status, HealthCheckResponse):
            console.print("[bold green]Server Health Status: Healthy[/bold green]")
            console.print(f"[bold]Timestamp:[/bold] {health_status.timestamp}")
            console.print(f"[bold]Uptime:[/bold] {health_status.uptime:.2f} seconds")
        else:
            console.print("[bold red]Failed to fetch server health status[/bold red]")
            console.print(f"[bold]Error Code:[/bold] {health_status.statusCode}")
            console.print(f"[bold]Error Message:[/bold] {health_status.statusMessage}")