"""Test that Walytis' core functionality works, quickly.

Make sure brenthy isn't running before you run these tests.
Make sure the brenthy docker image is up to date.
Don't run pytest yet, as test_joining() always fails then for some reason.
Simply execute this script instead.

If testing is interrupted and the docker container isn't closed properly
and the next time you run this script you get an error reading:
    docker: Error response from daemon: Conflict.
    The container name "/brenthy_test" is already in use by container

run the following commands to stop and remove the unterminated container:
    docker stop $(docker ps -aqf "name=^brenthy_test$")
    docker rm $(docker ps -aqf "name=^brenthy_test$")
"""

# This import allows us to run this script with either pytest or python
import _auto_run_with_pytest  # noqa
import walytis_beta_embedded
import pytest
import shutil
import os
from emtest import await_thread_cleanup
from testing_utils import shared_data

import testing_utils
NUMBER_OF_JOIN_ATTEMPTS = 10
DOCKER_CONTAINER_NAME = "brenthy_tests_walytis"
REBUILD_DOCKER = False
# enable/disable breakpoints when checking intermediate test results

# if you do not have any other important brenthy docker containers,
# you can set this to true to automatically remove unpurged docker containers
# after failed tests
DELETE_ALL_BRENTHY_DOCKERS = True
if True:
    # import run
    import run
    run.TRY_INSTALL = False
    import walytis_beta_api

    # print("PWB")




def test_preparations() -> None:
    """Get everything needed to run the tests ready."""
    false_id_path = os.path.join(
        walytis_beta_embedded.get_walytis_appdata_dir(), "FALSE_BLOCKCHAIN_ID"
    )
    if os.path.exists(false_id_path):
        shutil.rmtree(false_id_path)

    testing_utils.run_walytis()

    if "TestingWalytis" in walytis_beta_api.list_blockchain_names():
        walytis_beta_api.delete_blockchain("TestingWalytis")
    print("Finished preparations...")


def cleanup(request: pytest.FixtureRequest | None = None) -> None:
    """Clean up after running tests with PyTest."""
    testing_utils.stop_walytis()


def test_create_blockchain() -> None:
    """Test that we can create a Walytis blockchain."""
    testing_utils.test_create_blockchain()


def test_add_block() -> None:
    """Test that we can add a block to the blockchain."""
    testing_utils.test_add_block()


def test_create_invitation() -> None:
    """Test that we can create an invitation for the blockchain."""
    testing_utils.test_create_invitation()


def test_list_blockchains() -> None:
    """Test that getting a list of blockchains ids and names works."""
    testing_utils.test_list_blockchains()


def test_list_blockchains_names_first() -> None:
    """Test that getting a list of blockchains works with the names first."""
    testing_utils.test_list_blockchains_names_first()


def test_list_blockchain_ids() -> None:
    """Test that getting a list of blockchains ids."""
    testing_utils.test_list_blockchain_ids()


def test_list_blockchain_names() -> None:
    """Test that getting a list of blockchains names."""
    testing_utils.test_list_blockchain_names()


def test_delete_blockchain() -> None:
    """Test that we can delete a blockchain."""
    testing_utils.test_delete_blockchain()


def test_threads_cleanup() -> None:
    """Test that no threads are left running."""
    shared_data.blockchain.terminate()
    testing_utils.stop_walytis()
    assert await_thread_cleanup(timeout=5)
    cleanup()
