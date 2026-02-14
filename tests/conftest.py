"""Script for configuring tests.

Runs automatically when pytest runs a test before loading the test module.
"""

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
    configure_pytest_reporter,
)
import pytest
import os
import sys


PRINT_ERRORS = (
    True  # whether or not to print error messages after failed tests
)


os.chdir(WORKDIR)


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """Make changes to pytest's behaviour."""
    configure_pytest_reporter(config, print_errors=PRINT_ERRORS)
    terminal = config.pluginmanager.get_plugin("terminalreporter")
    if terminal:
        terminal.write_line(f"Python {sys.version.split(' ')[0]}")


def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: pytest.ExitCode,
) -> None:
    """Clean up after pytest has finished."""
    os._exit(int(exitstatus))  # force close terminating dangling threads


def get_rebuild_docker(default: bool):
    return env_vars.bool("TESTS_REBUILD_DOCKER", default=default)


if env_vars.bool("CONFTEST_LOAD_WALYTIS", default=True):
    print("Loading Walytis...")
    from testing_imports import load_walytis

    load_walytis()
else:
    print("NOT loading Walytis")
