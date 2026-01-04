import _auto_run_with_pytest  # noqa
from walytis_beta_tools.exceptions import NoSuchBlockchainError
import json
import os
from emtest import polite_wait

import pytest
import walytis_beta_api
from brenthy_docker import BrenthyDocker, delete_containers
from build_docker import build_docker_image
from docker_scripts import MESSAGE_1, MESSAGE_2, MESSAGE_3
from emtest import await_thread_cleanup
from testing_utils import get_rebuild_docker, run_walytis, stop_walytis
from walytis_beta_api import (
    Blockchain,
    delete_blockchain,
    list_blockchain_names,
)
from walytis_beta_tools._experimental.ipfs_interface import ipfs

# walytis_beta_api.log.PRINT_DEBUG = True
NUMBER_OF_JOIN_ATTEMPTS = 10
DOCKER_CONTAINER_NAME = "test_walytis_sync_2"
BLOCKCHAIN_NAME = "TestWalytisSync2"
REBUILD_DOCKER = False  # overriden by environment variable
REBUILD_DOCKER = get_rebuild_docker(REBUILD_DOCKER)  # override if EnvVar set

# if you do not have any other important brenthy docker containers,
# you can set this to true to automatically remove unpurged docker containers
# after failed tests
DELETE_ALL_BRENTHY_DOCKERS = True
SYNC_DUR = 55


class SharedData:
    """Structure for storing data shared between test functions."""

    def __init__(self):
        self.brenthy_docker_1: BrenthyDocker | None = None
        self.brenthy_docker_2: BrenthyDocker | None = None
        self.blockchain: Blockchain | None = None
        self.blockchain_id: str | None = None
        self.appdata_cid: str | None = None


shared_data = SharedData()


def test_preparations() -> None:
    """Get everything needed to run the tests ready."""
    if DELETE_ALL_BRENTHY_DOCKERS:
        delete_containers(
            image="local/brenthy_testing",
            container_name_substr=DOCKER_CONTAINER_NAME,
        )

    if REBUILD_DOCKER:
        print("Rebuilding docker image brenthy_testing...")
        build_docker_image(verbose=False)

    print("Creating docker containers...")
    shared_data.brenthy_docker_1 = BrenthyDocker(
        image="local/brenthy_testing",
        container_name=f"{DOCKER_CONTAINER_NAME}_1",
        auto_run=True,
    )
    shared_data.brenthy_docker_2 = BrenthyDocker(
        image="local/brenthy_testing",
        container_name=f"{DOCKER_CONTAINER_NAME}_2",
        auto_run=True,
    )
    run_walytis()


def test_create_blockchain() -> None:
    """Test that we can create a Walytis blockchain."""
    if BLOCKCHAIN_NAME in list_blockchain_names():
        delete_blockchain(BLOCKCHAIN_NAME)
    shared_data.blockchain = walytis_beta_api.Blockchain.create(
        BLOCKCHAIN_NAME,
        app_name="BrenthyTester",
        block_received_handler=None,
    )
    shared_data.blockchain_id = shared_data.blockchain.blockchain_id
    shared_data.blockchain.add_block(MESSAGE_1.encode())
    appdata_path = shared_data.blockchain.get_blockchain_data()
    assert os.path.isfile(appdata_path), "Got blockchain appdata."
    shared_data.appdata_cid = ipfs.files.publish(appdata_path)
    shared_data.blockchain.terminate()


DOCKER_CODE_PRELUDE = """
import os, sys
sys.path.append('/opt/Brenthy/Brenthy/blockchains/Walytis_Beta/tests/')
import docker_scripts
"""

DOCKER_1_PART_1 = (
    DOCKER_CODE_PRELUDE
    + """
docker_scripts.docker_1_part_1("BC_ID", "APPDATA_CID")
"""
)

DOCKER_2_PART_1 = (
    DOCKER_CODE_PRELUDE
    + """
docker_scripts.docker_2_part_1("BC_ID", "APPDATA_CID")
"""
)

DOCKER_1_PART_2 = (
    DOCKER_CODE_PRELUDE
    + """
docker_scripts.docker_1_part_2("BC_ID", "APPDATA_CID")"""
)

DOCKER_2_PART_2 = DOCKER_1_PART_2


def test_block_sync() -> None:
    """Test that blocks are synchronised between two live blockchain nodes."""
    if not shared_data.brenthy_docker_1 or not shared_data.brenthy_docker_2:
        pytest.skip("Brenthy dockers not created.")
    if not shared_data.blockchain_id:
        pytest.skip("blockchain_id not set.")
    if not shared_data.appdata_cid:
        pytest.skip("`appdata_cid` not set.")

    shared_data.brenthy_docker_1.run_python_code(
        DOCKER_1_PART_1.replace(
            "APPDATA_CID", shared_data.appdata_cid
        ).replace("BC_ID", shared_data.blockchain_id),
        print_output=True,
    )
    print("RAN 1-1")
    shared_data.brenthy_docker_1.stop()
    print("STOPPED 1")

    shared_data.brenthy_docker_2.run_python_code(
        DOCKER_2_PART_1.replace(
            "APPDATA_CID", shared_data.appdata_cid
        ).replace("BC_ID", shared_data.blockchain_id),
        print_output=True,
    )
    print("RAN 2-1")
    shared_data.brenthy_docker_2.stop()
    print("STOPPED 2")

    shared_data.brenthy_docker_1.start()
    print("RESTARTED 1")
    shared_data.brenthy_docker_2.start()
    print("RESTARTED 2")
    polite_wait(SYNC_DUR)
    print("WAITED")
    output = shared_data.brenthy_docker_1.run_python_code(
        DOCKER_1_PART_2.replace(
            "APPDATA_CID", shared_data.appdata_cid
        ).replace("BC_ID", shared_data.blockchain_id),
        print_output=True,
    )
    print("RAN 1-2")
    last_line = output.split("\n")[-1].strip()
    blocks_content = json.loads(last_line.replace("'", '"'))
    assert blocks_content == [
        MESSAGE_1,
        MESSAGE_2,
        MESSAGE_2,
        MESSAGE_2,
        MESSAGE_3,
        MESSAGE_3,
        MESSAGE_3,
    ], "docker_1 synchronised!"
    output = shared_data.brenthy_docker_2.run_python_code(
        DOCKER_2_PART_2.replace(
            "APPDATA_CID", shared_data.appdata_cid
        ).replace("BC_ID", shared_data.blockchain_id),
        print_output=True,
    )
    print("RAN 2-2")
    last_line = output.split("\n")[-1].strip()
    blocks_content = json.loads(last_line.replace("'", '"'))
    assert blocks_content == [
        MESSAGE_1,
        MESSAGE_2,
        MESSAGE_2,
        MESSAGE_2,
        MESSAGE_3,
        MESSAGE_3,
        MESSAGE_3,
    ], "docker_2 synchronised!"


def test_threads_cleanup() -> None:
    """Test that no threads are left running."""
    blockchain = shared_data.blockchain
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
    if shared_data.brenthy_docker_1:
        shared_data.brenthy_docker_1.delete()
    if shared_data.brenthy_docker_2:
        shared_data.brenthy_docker_2.delete()
