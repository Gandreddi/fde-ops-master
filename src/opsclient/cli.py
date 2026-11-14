"""The `ops` command. Try: ops list-users"""

import typer

from opsclient.client import DEFAULT_BASE_URL, OpsClient
from opsclient.errors import OpsClientError
from opsclient.models import User

app = typer.Typer(help="Ops Copilot command line.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Ops Copilot command line."""


@app.command("list-users")
def list_users(base_url: str = typer.Option(DEFAULT_BASE_URL, help="API address.")) -> None:
    """Print every user: id, username, name and email."""
    try:
        with OpsClient(base_url=base_url) as client:
            users = client.list(User, "/users")
    except OpsClientError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    for user in users:
        typer.echo(f"{user.id:>3}  {user.username:<18} {user.name:<26} {user.email}")
