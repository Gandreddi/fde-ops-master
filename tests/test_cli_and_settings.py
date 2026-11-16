import json
import logging

import pytest
import respx
from typer.testing import CliRunner

from opsclient.cli import app
from opsclient.logging_config import JsonFormatter
from opsclient.settings import Settings
from tests.conftest import BASE_URL, USER_JSON

runner = CliRunner()


def test_settings_have_safe_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPS_MAX_ATTEMPTS", raising=False)
    assert Settings(_env_file=None).max_attempts == 3


def test_settings_read_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPS_BASE_URL", BASE_URL)
    monkeypatch.setenv("OPS_TIMEOUT_SECONDS", "2.5")
    settings = Settings(_env_file=None)
    assert (settings.base_url, settings.timeout_seconds) == (BASE_URL, 2.5)


def test_cli_prints_users(mock_api: respx.MockRouter, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPS_BASE_URL", BASE_URL)
    mock_api.get("/users").respond(200, json=[USER_JSON])
    result = runner.invoke(app, ["list-users"])
    assert result.exit_code == 0
    assert "asha" in result.output and "Asha Rao" in result.output


def test_cli_shows_clean_error_and_exit_code_1(
    mock_api: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPS_BASE_URL", BASE_URL)
    monkeypatch.setenv("OPS_MAX_ATTEMPTS", "1")
    mock_api.get("/users").respond(404)
    result = runner.invoke(app, ["list-users"])
    assert result.exit_code == 1
    assert "Error: HTTP 404" in result.output
    assert "Traceback" not in result.output


def test_log_lines_are_json_with_extra_fields() -> None:
    record = logging.LogRecord(
        "opsclient", logging.INFO, __file__, 1, "request finished", None, None
    )
    record.status = 200
    line = json.loads(JsonFormatter().format(record))
    assert line["event"] == "request finished"
    assert line["level"] == "INFO"
    assert line["status"] == 200
