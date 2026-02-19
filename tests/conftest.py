"""Script for configuring tests.

Runs automatically when pytest runs a test before loading the test module.
"""

from emtest.log_utils import get_app_log_dir
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
    set_env_var,
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

# add source code paths to python's search paths
add_path_to_python(SRC_DIR)

logger_tests = logging.getLogger("Tests-Walytis")
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


if True:  # IMPORT ORDER MATTERS, stop linters from reordering
    set_env_var("WALY_LOG_DIR", "/opt/log", override=False)

    if env_vars.bool("CONFTEST_LOAD_WALYTIS", default=True):
        print("Loading Walytis...")
        from testing_imports import load_walytis

        load_walytis()
    else:
        print("NOT loading Walytis")

    from walytis_beta_tools.log import (
        file_handler,
        console_handler,
        formatter,
    )

    if file_handler:
        file_handler.setLevel(logging.DEBUG)

    plain_console_handler = logging.StreamHandler()
    plain_console_handler.setLevel(logging.DEBUG)

    LOG_DIR = get_app_log_dir("Walytis_Beta_Tests", "Waly")
    if LOG_DIR:
        file_handler_tests = logging.handlers.RotatingFileHandler(
            os.path.join(LOG_DIR, "Tests-Walytis.log"),
            maxBytes=4 * 1024 * 1024,
            backupCount=4,
        )

        file_handler_tests.setLevel(logging.DEBUG)
        file_handler_tests.setFormatter(formatter)

        logger_tests.addHandler(file_handler_tests)
        logger_pytest.addHandler(file_handler_tests)
    console_handler.setLevel(logging.DEBUG)
    logger_tests.addHandler(plain_console_handler)
    logger_pytest.addHandler(plain_console_handler)

    # add logging for IPFS-Toolkit
    from ipfs_tk_transmission.log import logger_transm, logger_conv

    LOG_DIR = get_app_log_dir("IPFS_TK", "Waly")
    if LOG_DIR:
        file_handler_ipfs = logging.handlers.RotatingFileHandler(
            os.path.join(LOG_DIR, "IPFS_TK.log"),
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
        )
        file_handler_ipfs.setLevel(logging.DEBUG)
        file_handler_ipfs.setFormatter(formatter)

        logger_transm.addHandler(file_handler_ipfs)
        logger_conv.addHandler(file_handler_ipfs)

    logger_conv.setLevel(logging.DEBUG)
    logger_transm.setLevel(logging.DEBUG)
