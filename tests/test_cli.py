from unittest.mock import patch
from lootscout import cli

@patch("lootscout.wizard.run_setup")
def test_setup_subcommand_calls_wizard(mock_setup):
    cli.main(["setup"])
    mock_setup.assert_called_once()

@patch("lootscout.main.run")
@patch("lootscout.config.load")
def test_default_command_runs_pipeline(mock_load, mock_run):
    cli.main([])           # no args = run
    mock_run.assert_called_once()

@patch("lootscout.main.run")
@patch("lootscout.config.load")
def test_run_subcommand_runs_pipeline(mock_load, mock_run):
    cli.main(["run"])
    mock_run.assert_called_once()

@patch("lootscout.status.run_status", return_value=2)
def test_status_subcommand_calls_status_and_returns_code(mock_status):
    rc = cli.main(["status"])
    mock_status.assert_called_once()
    assert rc == 2

@patch("lootscout.remove.run_remove", return_value=0)
def test_remove_subcommand_calls_remove(mock_remove):
    rc = cli.main(["remove"])
    mock_remove.assert_called_once()
    assert rc == 0

@patch("lootscout.remove.run_remove", return_value=0)
def test_uninstall_is_alias_for_remove(mock_remove):
    cli.main(["uninstall"])
    mock_remove.assert_called_once()

def test_unknown_command_returns_2():
    assert cli.main(["bogus"]) == 2
