"""Script for configuring tests.

Runs automatically when pytest runs a test before loading the test module.
"""

from datetime import datetime
import logging
from testing_paths import (
    WORKDIR,
    PROJ_DIR,
    SRC_DIR,
    EMBEDDED_DIR,
    BRENTHY_DIR,
    BRENTHY_DOCKER_DIR,
)
from emtest import env_vars
from emtest import (
    add_path_to_python,
    are_we_in_docker,
    env_vars,
    get_pytest_report_dirs,
    configure_pytest_reporter,
)
import pytest
import os
import sys


PRINT_ERRORS = (
    True  # whether or not to print error messages after failed tests
)

os.chdir(WORKDIR)

logger_tests = logging.getLogger("Tests-WalId")
logger_tests.setLevel(logging.DEBUG)
logger_pytest = logging.getLogger("Pytest")
logger_pytest.setLevel(logging.DEBUG)


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    """Make changes to pytest's behaviour."""
    configure_pytest_reporter(
        config, print_errors=PRINT_ERRORS, logger=logger_pytest
    )
    terminal = config.pluginmanager.get_plugin("terminalreporter")
    if terminal:
        terminal.write_line(f"Python {sys.version.split(' ')[0]}")


def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: pytest.ExitCode,
) -> None:
    """Clean up after pytest has finished."""
    os._exit(int(exitstatus))  # force close terminating dangling threads


@pytest.fixture(scope="module")
def test_module_name(request: pytest.FixtureRequest) -> None:
    """Get the name of the currently running test module."""
    module = request.module
    module_name = module.__name__
    print(module_name)
    return module_name


@pytest.fixture(scope="session")
def test_report_dirs(
    pytestconfig: pytest.Config,
) -> None:
    """Get the directories pytest is configured to write reports to."""
    return get_pytest_report_dirs(pytestconfig)


@pytest.fixture(scope="module", autouse=True)
def test_module_start_time(
    pytestconfig: pytest.Config,
) -> None:
    """Get the time the currently running test module started."""
    return datetime.now()


def get_rebuild_docker(default: bool):
    return env_vars.bool("TESTS_REBUILD_DOCKER", default=default)


if env_vars.bool("CONFTEST_LOAD_WALYTIS", default=True):
    print("Loading Walytis...")
    from testing_imports import load_walytis

    load_walytis()
else:
    print("NOT loading Walytis")
