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
import _auto_run_with_pytest  # noqa
from conftest import BRENTHY_DIR, WalytisTestModes
from walytis_beta_tools._experimental.config import get_walytis_test_mode
import walytis_beta_embedded
import pytest
import time
import sys
import shutil
import os
from emtest import await_thread_cleanup
from walytis_beta_tools._experimental.ipfs_interface import ipfs

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

    from brenthy_docker import BrenthyDocker, delete_containers
    from build_docker import build_docker_image
    from walytis_beta_api import Block, Blockchain
    
    # walytis_beta_api.log.PRINT_DEBUG = True

brenthy_docker: BrenthyDocker
blockchain: Blockchain
invitation = ""
created_block: Block


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    """Wrap around tests, running preparations and cleaning up afterwards.

    A module-level fixture that runs once for all tests in this file.
    """
    # Setup: code here runs before tests that uses this fixture
    print(f"\nRunning tests for {__name__}\n")
    prepare()

    yield  # This separates setup from teardown

    # Teardown: code here runs after the tests
    print(f"\nFinished tests for {__name__}\n")
    cleanup()


def prepare() -> None:
    """Get everything needed to run the tests ready."""
    global brenthy_docker
    if DELETE_ALL_BRENTHY_DOCKERS:
        delete_containers(image="local/brenthy_testing",
                          container_name_substr="brenthy_tests_")

    if REBUILD_DOCKER:
        build_docker_image(verbose=False)
    false_id_path = os.path.join(
        walytis_beta_embedded.get_walytis_appdata_dir(), "FALSE_BLOCKCHAIN_ID"
    )
    if os.path.exists(false_id_path):
        shutil.rmtree(false_id_path)

    brenthy_docker = BrenthyDocker(
        image="local/brenthy_testing",
        container_name=DOCKER_CONTAINER_NAME,
        auto_run=False
    )
    run_walytis()
    
    if "TestingWalytis" in walytis_beta_api.list_blockchain_names():
        walytis_beta_api.delete_blockchain("TestingWalytis")
    print("Finished preparations...")


def cleanup(request: pytest.FixtureRequest | None = None) -> None:
    """Clean up after running tests with PyTest."""
    brenthy_docker.stop()
    # _testing_utils.terminate()

    stop_walytis()

WALYTIS_TEST_MODE= get_walytis_test_mode()
def run_walytis() -> None:
    """Test that we can run Brenthy-Core."""
    global WALYTIS_TEST_MODE
    match WALYTIS_TEST_MODE:
        case WalytisTestModes.RUN_BRENTHY:
            # run.log.set_print_level("important")
            print("Running Brenthy...")
            run.run_brenthy()
        case WalytisTestModes.EMBEDDED:
            print("Running Walytis embedded...")
            walytis_beta_embedded.run_blockchains()
            print("Running Walytis embedded.")
        case WalytisTestModes.USE_BRENTHY:
            pass
        case _:
            raise Exception("BUG in handling of WALYTIS_TEST_MODE!")
def stop_walytis() -> None:
    """Stop Brenthy-Core."""
    match WALYTIS_TEST_MODE:
        case WalytisTestModes.RUN_BRENTHY:
            run.stop_brenthy()
        case WalytisTestModes.EMBEDDED:
            walytis_beta_embedded.terminate()
        case WalytisTestModes.USE_BRENTHY:
            pass
        case _:
            raise Exception("BUG in handling of WALYTIS_TEST_MODE!")


def on_block_received(block: Block) -> None:
    """Eventhandler for newly created blocks on the test's blockchain."""
    global created_block
    created_block = block



def test_run_docker() -> None:
    """Test that we can run the Brenthy docker container."""
    try:
        brenthy_docker.start()
        assert True, "Run BrenthyDocker"
        
    except Exception as e:
        assert False, "Failed to run BrenthyDocker"
        print(e)
        sys.exit()


def test_find_peer() -> None:
    """Test that we are connected to the Brenthy docker container via IPFS."""
    brenthy_docker.start()
    success = False
    for i in range(5):
        success = ipfs.peers.find(brenthy_docker.ipfs_id)
        if success:
            break

    assert success, "ipfs.peers.find"


def test_create_blockchain() -> None:
    """Test that we can create a Walytis blockchain."""
    global blockchain
    blockchain = walytis_beta_api.Blockchain.create(
        "TestingWalytis",
        app_name="BrenthyTester",
        block_received_handler=on_block_received,
    )
    
    success = isinstance(blockchain, walytis_beta_api.Blockchain)
    assert success, "create_blockchain"

    time.sleep(2)


def test_add_block() -> None:
    """Test that we can add a block to the blockchain."""
    block = blockchain.add_block("Hello there!".encode())
    success = (
        block.short_id in blockchain._blocks.get_short_ids() and
        block.long_id in blockchain._blocks.get_long_ids() and
        blockchain.get_block(
            blockchain._blocks.get_short_ids()[-1]).content.decode()
        == blockchain.get_block(blockchain._blocks.get_long_ids()[-1]).content.decode()
        == "Hello there!"
    )
    assert success, "Blockchain.add_block"


def test_create_invitation() -> None:
    """Test that we can create an invitation for the blockchain."""
    global invitation
    invitation = blockchain.create_invitation(one_time=False)
    success = (
        invitation in blockchain.get_invitations(),
        "newly created invitation is not listed in blockchain's invitations",
    )
    assert success, "Blockchain.create_invitation"


def test_joining() -> None:
    """Test that another node can join the blockchain."""
    if not invitation:
        raise CantRunTestError("Invitation is blank")

    join_python_code = (
        f"""
import walytis_beta_api
try:
    walytis_beta_api.join_blockchain('{invitation}')
except Exception as e:
    print(e)
"""
    )
    test_python_code = ";".join([
        "import walytis_beta_api",
        f"print('{blockchain.blockchain_id}' in "
        "walytis_beta_api.list_blockchain_ids())"
    ]
    )

    result = "-"
    for i in range(NUMBER_OF_JOIN_ATTEMPTS):
        result = brenthy_docker.run_python_code(
            join_python_code, print_output=True)
        print(result)
        lines = brenthy_docker.run_python_code(
            test_python_code, print_output=False
        ).split("\n")
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
            os.path.join(
                BRENTHY_DIR, "InstallScripts", "BrenthyUpdates.zip"
            ),
        )
    except walytis_beta_api.JoinFailureError:
        exception = True
    success = "FALSE_BLOCKCHAIN_ID" not in walytis_beta_api.list_blockchains()
    assert success and exception, "join blockchain ID check"


def test_delete_blockchain() -> None:
    """Test that we can delete a blockchain."""
    blockchain.terminate()
    walytis_beta_api.delete_blockchain("TestingWalytis")
    success = (
        "TestingWalytis" not in walytis_beta_api.list_blockchain_names(),
        "failed to delete blockchain",
    )
    assert success, "delete_blockchain"


def test_threads_cleanup() -> None:
    brenthy_docker.stop()
    blockchain.terminate()
    stop_walytis()
    assert await_thread_cleanup(timeout=5)
#
#
# def test_list_blockchains() -> None:
#     """Test that getting a list of blockchains IDs and names works."""
#     walytis_beta_api.list_blockchains()
#
#     found = False
#     for id, name in walytis_beta_api.list_blockchains():
#         if id == blockchain.blockchain_id and name == blockchain.name:
#             found = True
#             break
#     mark(found, "walytis_beta_api.list_blockchains")
#
#
# def test_list_blockchains_names_first() -> None:
#     """Test that getting a list of blockchains works with the names first."""
#     all_in_order = walytis_beta_api.list_blockchains(names_first=True) == [
#         (name, id) for id, name in walytis_beta_api.list_blockchains()
#     ]
#     mark(all_in_order,
#          "walytis_beta_api.list_blockchains(names_first=True)",
#          )
#
#
# def test_list_blockchain_ids() -> None:
#     """Test that getting a list of blockchains IDs."""
#     all_in_order = (
#         blockchain.blockchain_id in walytis_beta_api.list_blockchain_ids()
#         and walytis_beta_api.list_blockchain_ids()
#         == [id for id, name in walytis_beta_api.list_blockchains()]
#     )
#     mark(all_in_order, "walytis_beta_api.list_blockchain_ids")
#
#
# def test_list_blockchain_names() -> None:
#     """Test that getting a list of blockchains names."""
#     all_in_order = (
#         blockchain.name in walytis_beta_api.list_blockchain_names()
#         and walytis_beta_api.list_blockchain_names()
#         == [name for id, name in walytis_beta_api.list_blockchains()]
#     )
#     mark(all_in_order, "walytis_beta_api.list_blockchain_names")


class CantRunTestError(Exception):
    """When we can't run tests for some reason."""

    def __init__(self, message: str = ""):
        self.message = message

    def __str__(self):
        return self.message


def run_tests() -> None:
    """Run all tests."""
    prepare()
    print("\nRunning thorough tests for walytis_beta...")
    test_run_walytis()

    brenthy_docker.start()

    test_find_peer()
    test_create_blockchain()
    test_add_block()
    test_create_invitation()
    test_joining()
    test_join_id_check()
    test_delete_blockchain()
    # breakpoint()
    brenthy_docker.stop()
    blockchain.terminate()
    stop_walytis()
    test_threads_cleanup()
