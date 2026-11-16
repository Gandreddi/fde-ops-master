"""The `ops` command. Try: ops list-users"""

import typer

from opsclient.client import OpsClient
from opsclient.errors import OpsClientError
from opsclient.logging_config import configure_logging
from opsclient.models import User
from opsclient.settings import Settings

app = typer.Typer(help="Ops Copilot command line.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Ops Copilot command line."""


@app.command("list-users")
def list_users(
    base_url: str | None = typer.Option(None, help="API address. Default: OPS_BASE_URL."),
) -> None:
    """Print every user: id, username, name and email."""
    settings = Settings()
    configure_logging(settings.log_level)
    try:
        with OpsClient(
            base_url=base_url or settings.base_url,
            timeout=settings.timeout_seconds,
            max_attempts=settings.max_attempts,
        ) as client:
            users = client.list(User, "/users")
    except OpsClientError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    for user in users:
        typer.echo(f"{user.id:>3}  {user.username:<18} {user.name:<26} {user.email}")
