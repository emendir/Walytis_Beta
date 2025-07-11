"""Script for configuring tests.

Runs automatically when pytest runs a test before loading the test module.
"""
from enum import Enum
from dataclasses import dataclass
from brenthy_docker.brenthy_docker import BrenthyDocker
from environs import Env
import pytest
import os

from emtest import add_path_to_python, configure_pytest_reporter

PRINT_ERRORS = True  # whether or not to print error messages after failed tests

# add source code paths to python's search paths
PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(
    PROJ_DIR, "src"
)
EMBEDDED_DIR = os.path.join(
    PROJ_DIR, "legacy_packaging", "walytis_beta_embedded"
)
BRENTHY_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "..", "..", "..",  "Brenthy"
)
BRENTHY_DOCKER_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "..", "..", "..", "tests", "brenthy_docker"
))
add_path_to_python(SRC_DIR)
add_path_to_python(EMBEDDED_DIR)
add_path_to_python(BRENTHY_DIR)
add_path_to_python(BRENTHY_DOCKER_DIR)


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """Make changes to pytest's behaviour."""
    configure_pytest_reporter(config, print_errors=PRINT_ERRORS)


WE_ARE_IN_DOCKER = os.path.exists('/.dockerenv')



from walytis_beta_tools._experimental.config import WalytisTestModes, get_walytis_test_mode, get_ipfs_tk_mode


if get_walytis_test_mode() == WalytisTestModes.EMBEDDED:
    os.environ["WALYTIS_BETA_API_TYPE"] = "WALYTIS_BETA_DIRECT_API"
if WE_ARE_IN_DOCKER:
    WALYTIS_TEST_MODE = WalytisTestModes.USE_BRENTHY
# print("WALYTIS_TEST_MODE:", WALYTIS_TEST_MODE)
# print("IPFS_TK_MODE:     ", IPFS_TK_MODE)
if True:
    # ensure IPFS is initialised via Walytis_Beta.networking, not walytis_beta_api
    import walytis_beta_api
    import walytis_beta_embedded
    import walytis_beta_tools
    from emtest import assert_is_loaded_from_source
    assert_is_loaded_from_source(EMBEDDED_DIR, walytis_beta_embedded)
    assert_is_loaded_from_source(SRC_DIR, walytis_beta_api)
    assert_is_loaded_from_source(SRC_DIR, walytis_beta_tools)
    walytis_beta_embedded.set_appdata_dir("./.blockchains")



