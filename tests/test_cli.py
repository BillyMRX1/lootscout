from unittest.mock import patch
from free_checker import cli

@patch("free_checker.wizard.run_setup")
def test_setup_subcommand_calls_wizard(mock_setup):
    cli.main(["setup"])
    mock_setup.assert_called_once()

@patch("free_checker.main.run")
@patch("free_checker.config.load")
def test_default_command_runs_pipeline(mock_load, mock_run):
    cli.main([])           # no args = run
    mock_run.assert_called_once()

@patch("free_checker.main.run")
@patch("free_checker.config.load")
def test_run_subcommand_runs_pipeline(mock_load, mock_run):
    cli.main(["run"])
    mock_run.assert_called_once()
