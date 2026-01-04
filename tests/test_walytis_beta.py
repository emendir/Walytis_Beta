"""Test that Walytis' core functionality works, using docker containers.

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
import os
import shutil

import _auto_run_with_pytest  # noqa
import pytest
import testing_utils
import walytis_beta_embedded
from conftest import BRENTHY_DIR
from emtest import await_thread_cleanup
from testing_utils import get_rebuild_docker, shared_data
from walytis_beta_tools._experimental.ipfs_interface import ipfs

NUMBER_OF_JOIN_ATTEMPTS = 10
DOCKER_CONTAINER_NAME = "brenthy_tests_walytis"
REBUILD_DOCKER = True  # overriden by environment variable
REBUILD_DOCKER = get_rebuild_docker(REBUILD_DOCKER)  # override if EnvVar set
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
    from brenthy_docker.brenthy_docker import BrenthyDocker, delete_containers
    from build_docker import build_docker_image

    # walytis_beta_api.log.PRINT_DEBUG = True


# @pytest.fixture(scope="module", autouse=True)
# def setup_and_teardown() -> None:
#     """Wrap around tests, running preparations and cleaning up afterwards.
#
#     A module-level fixture that runs once for all tests in this file.
#     """
#     # Setup: code here runs before tests that uses this fixture
#     print(f"\nRunning tests for {__name__}\n")
#     prepare()
#
#     yield  # This separates setup from teardown
#
#     # Teardown: code here runs after the tests
#     print(f"\nFinished tests for {__name__}\n")
#     cleanup()


def test_preparations() -> None:
    """Get everything needed to run the tests ready."""
    if DELETE_ALL_BRENTHY_DOCKERS:
        delete_containers(
            image="local/brenthy_testing",
            container_name_substr=DOCKER_CONTAINER_NAME,
        )

    if REBUILD_DOCKER:
        build_docker_image(verbose=False)
    false_id_path = os.path.join(
        walytis_beta_embedded.get_walytis_appdata_dir(), "FALSE_BLOCKCHAIN_ID"
    )
    if os.path.exists(false_id_path):
        shutil.rmtree(false_id_path)

    shared_data.brenthy_dockers = []
    shared_data.brenthy_dockers.append(
        BrenthyDocker(
            image="local/brenthy_testing",
            container_name=DOCKER_CONTAINER_NAME,
            auto_run=False,
        )
    )
    testing_utils.run_walytis()

    if "TestingWalytis" in walytis_beta_api.list_blockchain_names():
        walytis_beta_api.delete_blockchain("TestingWalytis")
    print("Finished preparations...")


def cleanup(request: pytest.FixtureRequest | None = None) -> None:
    """Clean up after running tests with PyTest."""
    shared_data.brenthy_dockers[0].stop()
    # _testing_utils.terminate()

    testing_utils.stop_walytis()


def test_find_peer() -> None:
    """Test that we are connected to the Brenthy docker container via IPFS."""
    shared_data.brenthy_dockers[0].start()
    success = False
    for i in range(5):
        success = ipfs.peers.find(shared_data.brenthy_dockers[0].ipfs_id)
        if success:
            break

    assert success, "ipfs.peers.find"


def test_create_blockchain() -> None:
    """Test that we can create a Walytis blockchain."""
    testing_utils.test_create_blockchain()


def test_add_block() -> None:
    """Test that we can add a block to the blockchain."""
    testing_utils.test_add_block()


def test_create_invitation() -> None:
    """Test that we can create an invitation for the blockchain."""
    testing_utils.test_create_invitation()


def test_joining() -> None:
    """Test that another node can join the blockchain."""
    if not shared_data.invitation:
        pytest.skip("Invitation is blank")

    join_python_code = f"""
import walytis_beta_api
try:
    walytis_beta_api.join_blockchain('{shared_data.invitation}')
except Exception as e:
    print(e)
"""
    test_python_code = ";".join(
        [
            "import walytis_beta_api",
            f"print('{shared_data.blockchain.blockchain_id}' in "
            "walytis_beta_api.list_blockchain_ids())",
        ]
    )

    result = "-"
    for i in range(NUMBER_OF_JOIN_ATTEMPTS):
        result = shared_data.brenthy_dockers[0].run_python_code(
            join_python_code, print_output=True
        )
        print(result)
        lines = (
            shared_data.brenthy_dockers[0]
            .run_python_code(test_python_code, print_output=False)
            .split("\n")
        )
        if lines:
            result = lines[-1].strip("\n")
            if result == "True":
                break

    success = result == "True"
    assert success, "join_blockchain"


def test_join_id_check() -> None:
    """Test that Walytis detects mismatched blockchain IDs when joining."""
    exception = False
    try:
        walytis_beta_api.join_blockchain_from_zip(
            "FALSE_BLOCKCHAIN_ID",
            os.path.join(BRENTHY_DIR, "InstallScripts", "BrenthyUpdates.zip"),
        )
    except walytis_beta_api.JoinFailureError:
        exception = True
    success = "FALSE_BLOCKCHAIN_ID" not in walytis_beta_api.list_blockchains()
    assert success and exception, "join blockchain ID check"


def test_delete_blockchain() -> None:
    """Test that we can delete a blockchain."""
    testing_utils.test_delete_blockchain()


def test_threads_cleanup() -> None:
    """Test that no threads are left running."""
    shared_data.brenthy_dockers[0].stop()
    shared_data.blockchain.terminate()
    testing_utils.stop_walytis()
    assert await_thread_cleanup(timeout=5)
    cleanup()
