"""Test that Walytis blockchains' blocks get synchronised across nodes.

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

import _auto_run_with_pytest  # noqa
import testing_utils
from emtest import await_thread_cleanup
from emtest import polite_wait
from walytis_beta_tools.exceptions import NoSuchBlockchainError
from walytis_beta_tools._experimental.ipfs_interface import ipfs
import pytest
from testing_utils import run_walytis, stop_walytis
import time
from brenthy_tools_beta import log
import walytis_beta_api
from walytis_beta_api import Block
from threading import Thread
from testing_utils import shared_data
from build_docker import build_docker_image
from brenthy_docker import BrenthyDocker, delete_containers
from testing_utils import get_rebuild_docker

REBUILD_DOCKER = False  # overriden by environment variable
REBUILD_DOCKER = get_rebuild_docker(REBUILD_DOCKER)  # override if EnvVar set
NUMBER_OF_FIND_ATTEMPTS = 10
NUMBER_OF_JOIN_ATTEMPTS = 10
DOCKER_CONTAINER_NAME = "test_walytis_sync_1"
NUMBER_OF_CONTAINERS = 5
# enable/disable breakpoints when checking intermediate test results

# automatically remove all docker containers after failed tests
DELETE_ALL_BRENTHY_DOCKERS = True


if True:
    # import run
    import run

    run.TRY_INSTALL = False
    import walytis_beta_api

    # print("PWB")
    from brenthy_docker.brenthy_docker import BrenthyDocker, delete_containers
    from build_docker import build_docker_image


def test_preparations() -> None:
    """Get everything needed to run the tests ready."""
    if DELETE_ALL_BRENTHY_DOCKERS:
        print("Deleting docker containers...")
        delete_containers(
            image="local/brenthy_testing",
            container_name_substr=DOCKER_CONTAINER_NAME,
        )

    if REBUILD_DOCKER:
        build_docker_image(verbose=False)

    # create the docker containers we will run tests with,
    # but don't run brenthy on them yet
    print("Preparing Docker containers...")
    shared_data.brenthy_dockers = []
    for i in range(NUMBER_OF_CONTAINERS):
        shared_data.brenthy_dockers.append(
            BrenthyDocker(
                image="local/brenthy_testing",
                container_name=DOCKER_CONTAINER_NAME + "0" + str(i),
                auto_run=False,
            )
        )
    print("Running Walytis...")
    run_walytis()  # run brenthy on this operating system
    print("Deleting old blockchains...")
    # if "TestingOnboarding" in walytis_beta_api.list_blockchain_names():
    #     walytis_beta_api.delete_blockchain("TestingOnboarding")
    testing_utils.delete_blockchains()  # clean up after failed tests


def on_block_received(block: Block) -> None:
    """Eventhandler for newly created blocks on the test's blockchain."""
    pass


def get_docker_latest_block_content(
    docker_container: BrenthyDocker,
) -> str:
    """Get the content of the latest block on the specified container."""
    return docker_container.run_python_code(
        ";".join(
            [
                "import walytis_beta_api",
                f"bc = walytis_beta_api.Blockchain("
                f"'{shared_data.blockchain.blockchain_id}')",
                "print(bc.get_block(-1).content.decode())",
                "bc.terminate()",
            ]
        ),
        print_output=False,
    ).strip("\n")


def ipfs_connect_to_container(index: int) -> bool:
    """Try to connect to the specified docker container via IPFS."""
    for i in range(NUMBER_OF_FIND_ATTEMPTS):
        if ipfs.peers.find(shared_data.brenthy_dockers[index].ipfs_id):
            return True
    return False


def docker_join_blockchain(index: int) -> bool:
    """Try to make the specified docker container join the test blockchain."""
    blockchain = shared_data.blockchain
    if not blockchain:
        pytest.skip("No blockchain created.")
    brenthy_dockers = shared_data.brenthy_dockers
    invitation = blockchain.create_invitation(one_time=False, shared=True)
    join_python_code = (
        "import walytis_beta_api;"
        f"walytis_beta_api.join_blockchain('{invitation}')"
    )
    test_join_python_code = (
        "import walytis_beta_api;"
        f"print('{blockchain.blockchain_id}' in "
        "walytis_beta_api.list_blockchain_ids())"
    )
    for i in range(NUMBER_OF_JOIN_ATTEMPTS):
        brenthy_dockers[index].run_python_code(
            join_python_code, print_output=False
        )
        result = (
            brenthy_dockers[index]
            .run_python_code(test_join_python_code, print_output=False)
            .split("\n")[-1]
        )

        if result == "True":
            if i > 0:
                print("Number of failed join attempts:", i)
            return True
    return False


def test_sync_block_creation() -> None:
    """Test that blocks are synchronised to other nodes when created."""
    brenthy_dockers = shared_data.brenthy_dockers
    shared_data.blockchain = walytis_beta_api.Blockchain.create(
        "TestingOnboarding",
        block_received_handler=on_block_received,
        app_name="test_onboarding.py",
    )
    blockchain = testing_utils.shared_data.blockchain

    brenthy_dockers[0].start()
    assert ipfs_connect_to_container(0), "ipfs.peers.find"
    assert docker_join_blockchain(0), "join_blockchain"

    blockchain.add_block("DUMMY".encode())
    blockchain.add_block("Test1".encode())
    for _ in range(2):
        time.sleep(5)
        result = get_docker_latest_block_content(brenthy_dockers[0])
        result = [line for line in result.split("\n") if line][-1]
        success = result == "Test1"
        if success:
            break
    assert success, "synchronised to peer on block creation"
    brenthy_dockers[0].stop()


def test_sync_on_join() -> None:
    """Test that blocks are synchronised to other nodes when joining."""
    blockchain = shared_data.blockchain
    if not blockchain:
        pytest.skip("No blockchain created.")
    brenthy_dockers = shared_data.brenthy_dockers
    time.sleep(2)
    brenthy_dockers[1].start()

    assert ipfs_connect_to_container(1), "ipfs.peers.find"
    assert docker_join_blockchain(1), "join_blockchain"

    for _ in range(3):
        polite_wait(5)
        print("Getting docker's latest block...")
        result = get_docker_latest_block_content(brenthy_dockers[1])
        result = [line for line in result.split("\n") if line][-1]

        success = result == "Test1"
        if success:
            break
    assert success, "synchronised to peer on joining"


def test_sync_on_awake() -> None:
    """Test that blocks are synchronised to other nodes when coming online."""
    blockchain = shared_data.blockchain
    if not blockchain:
        pytest.skip("No blockchain created.")
    brenthy_dockers = shared_data.brenthy_dockers
    # test getting latest blocks on awaking
    brenthy_dockers[1].stop()
    blockchain.add_block("DUMMY".encode())
    blockchain.add_block("Test2".encode())
    polite_wait(10)
    brenthy_dockers[1].restart()
    for i in range(6):
        polite_wait(5)
        result = get_docker_latest_block_content(brenthy_dockers[1])
        result = [line for line in result.split("\n") if line][-1]
        success = result == "Test2"
        if success:
            break
    assert success, "synchronised to peer on awaking"


def test_get_peers() -> None:
    """Test that we can get a list of connected nodes."""
    blockchain = shared_data.blockchain
    if not blockchain:
        pytest.skip("No blockchain created.")
    brenthy_dockers = shared_data.brenthy_dockers
    for container in brenthy_dockers:
        # container.start()
        container.restart()
    polite_wait(20)
    peers = blockchain.get_peers()

    # we're testing for if ANY docker peer is listed, because
    # IPFS' pubsub HTTP RPC system isn't reliable enough to test if ALL are
    peers_found = False
    for container in brenthy_dockers:
        if container.ipfs_id in peers:
            peers_found = True
    assert peers_found, "get_peers"


def test_threads_cleanup() -> None:
    """Test that no threads are left running."""
    blockchain = shared_data.blockchain
    log.debug("test: deleting blockhain")
    if blockchain:
        blockchain.terminate()
        try:
            walytis_beta_api.delete_blockchain(blockchain.blockchain_id)
        except NoSuchBlockchainError:
            pass
    stop_walytis()
    assert await_thread_cleanup(), "Threads clean up"
    cleanup()


def cleanup() -> None:
    """Ensure all resources used by tests are cleaned up."""
    blockchain = shared_data.blockchain
    brenthy_dockers = shared_data.brenthy_dockers
    log.debug("test: deleting blockhain")
    if blockchain:
        blockchain.terminate()
        try:
            walytis_beta_api.delete_blockchain(blockchain.blockchain_id)
        except NoSuchBlockchainError:
            pass
    # Terminate Docker containers and our test brenthy instance in parallel
    termination_threads = []
    # start terminating docker containers
    for docker in brenthy_dockers:
        termination_threads.append(
            Thread(target=BrenthyDocker.stop, args=(docker,))
        )
        termination_threads[-1].start()
    # terminate our own brenthy instance
    # wair till all docker containers are terminated
    for thread in termination_threads:
        thread.join()
