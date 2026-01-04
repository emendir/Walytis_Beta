from emtest import polite_wait
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from brenthy_tools_beta.utils import time_to_string, string_to_time

if True:
    import _auto_run_with_pytest  # noqa

    from conftest import get_rebuild_docker

    from emtest import await_thread_cleanup
    from build_docker import build_docker_image

    from brenthy_docker import BrenthyDocker, delete_containers

    import pytest
    from datetime import timedelta


# walytis_beta_api.log.PRINT_DEBUG = True
NUMBER_OF_JOIN_ATTEMPTS = 10
DOCKER_CONTAINER_NAME = "test_walytis_clocks"
REBUILD_DOCKER = False  # overriden by environment variable
REBUILD_DOCKER = get_rebuild_docker(REBUILD_DOCKER)  # override if EnvVar set

# if you do not have any other important brenthy docker containers,
# you can set this to true to automatically remove unpurged docker containers
# after failed tests
DELETE_ALL_BRENTHY_DOCKERS = True
SYNC_DUR = 50

PYTHON_FAKETIME_CMD = (
    "set -a && source /opt/Brenthy/Brenthy.env && set +a && /bin/python3"
)

TIMEDELTA = timedelta(days=1)


@dataclass
class BlockchainInfo:
    blockchain_id: str
    appdata_cid: str
    creation_time: datetime


class SharedData:
    """Structure for storing data shared between test functions."""

    def __init__(self):
        self.brenthy_docker_1: BrenthyDocker | None = None
        self.brenthy_docker_2: BrenthyDocker | None = None
        self.brenthy_docker_3: BrenthyDocker | None = None
        self.blockchain_id: str | None = None
        self.appdata_cid: str | None = None
        self.blockchain_1: BlockchainInfo | None = None
        self.blockchain_2: BlockchainInfo | None = None
        self.blockchain_3: BlockchainInfo | None = None


shared_data = SharedData()


def test_preparations() -> None:
    """Get everything needed to run the tests ready."""
    print("Running preps...")
    if DELETE_ALL_BRENTHY_DOCKERS:
        delete_containers(
            image="local/brenthy_testing",
            container_name_substr=DOCKER_CONTAINER_NAME,
        )

    if REBUILD_DOCKER:
        build_docker_image(verbose=False)
    print("Creating docker containers...")

    # skip IPFS check to avoid dependence
    shared_data.brenthy_docker_2 = BrenthyDocker(
        image="local/brenthy_testing",
        container_name=f"{DOCKER_CONTAINER_NAME}_2",
        auto_run=True,
        await_ipfs=False,
        await_brenthy=False,
    )
    shared_data.brenthy_docker_3 = BrenthyDocker(
        image="local/brenthy_testing",
        container_name=f"{DOCKER_CONTAINER_NAME}_3",
        auto_run=True,
        await_ipfs=False,
        await_brenthy=False,
    )
    shared_data.brenthy_docker_1 = BrenthyDocker(
        image="local/brenthy_testing",
        container_name=f"{DOCKER_CONTAINER_NAME}_1",
        auto_run=True,
        await_ipfs=False,
        await_brenthy=False,
    )

    # Wait till brenthy update blockchain migration for docker has completed
    shared_data.brenthy_docker_2.await_brenthy()
    shared_data.brenthy_docker_3.await_brenthy()

    shared_data.brenthy_docker_2.set_brenthy_clock_offset(TIMEDELTA)
    shared_data.brenthy_docker_3.set_brenthy_clock_offset(-1 * TIMEDELTA)

    shared_data.brenthy_docker_1.await_brenthy()

    # ensure each BrenthyDocker object knows its IPFS peer ID
    shared_data.brenthy_docker_1.get_ipfs_id()
    shared_data.brenthy_docker_2.get_ipfs_id()
    shared_data.brenthy_docker_3.get_ipfs_id()


def test_create_blockchains():
    shared_data.blockchain_1 = docker_create_blockchain(
        shared_data.brenthy_docker_1
    )
    shared_data.blockchain_2 = docker_create_blockchain(
        shared_data.brenthy_docker_2
    )
    shared_data.blockchain_3 = docker_create_blockchain(
        shared_data.brenthy_docker_3
    )
    blockchain_1 = shared_data.blockchain_1
    blockchain_2 = shared_data.blockchain_2
    blockchain_3 = shared_data.blockchain_3
    assert (
        blockchain_1.blockchain_id
        != blockchain_2.blockchain_id
        != blockchain_3.blockchain_id
    )
    assert (
        blockchain_1.appdata_cid
        != blockchain_2.appdata_cid
        != blockchain_3.appdata_cid
    )


def test_clocks_are_desynced():
    assert (
        shared_data.blockchain_2.creation_time
        - shared_data.blockchain_1.creation_time
        > 0.9 * TIMEDELTA
    )
    assert (
        shared_data.blockchain_1.creation_time
        - shared_data.blockchain_3.creation_time
        > 0.9 * TIMEDELTA
    )


def test_join_blockchains():
    print("Joining on container 1 from blockchain of container 2...")
    docker_join_blockchain(
        shared_data.brenthy_docker_1, shared_data.blockchain_2
    )
    print("Joining on container 1 from blockchain of container 3...")
    docker_join_blockchain(
        shared_data.brenthy_docker_1, shared_data.blockchain_3
    )
    print("Joining on container 2 from blockchain of container 1...")
    docker_join_blockchain(
        shared_data.brenthy_docker_2, shared_data.blockchain_1
    )
    print("Joining on container 2 from blockchain of container 3...")
    docker_join_blockchain(
        shared_data.brenthy_docker_2, shared_data.blockchain_3
    )
    print("Joining on container 3 from blockchain of container 2...")
    docker_join_blockchain(
        shared_data.brenthy_docker_3, shared_data.blockchain_2
    )
    print("Joining on container 3 from blockchain of container 1...")
    docker_join_blockchain(
        shared_data.brenthy_docker_3, shared_data.blockchain_1
    )


def test_block_sync():
    polite_wait(SYNC_DUR)
    brenthy_docker_1 = shared_data.brenthy_docker_1
    brenthy_docker_2 = shared_data.brenthy_docker_2
    brenthy_docker_3 = shared_data.brenthy_docker_3
    blockchain_1 = shared_data.blockchain_1
    blockchain_2 = shared_data.blockchain_2
    blockchain_3 = shared_data.blockchain_3

    assert docker_check_blocks(brenthy_docker_1, blockchain_1)
    assert docker_check_blocks(brenthy_docker_1, blockchain_2)
    assert docker_check_blocks(brenthy_docker_1, blockchain_3)

    assert docker_check_blocks(brenthy_docker_2, blockchain_1)
    assert docker_check_blocks(brenthy_docker_2, blockchain_2)
    assert docker_check_blocks(brenthy_docker_2, blockchain_3)

    assert docker_check_blocks(brenthy_docker_3, blockchain_1)
    assert docker_check_blocks(brenthy_docker_3, blockchain_2)
    assert docker_check_blocks(brenthy_docker_3, blockchain_3)


DOCKER_CODE_PRELUDE = """
import os, sys
sys.path.append('/opt/Brenthy/Brenthy/blockchains/Walytis_Beta/tests/')
import docker_scripts
"""

DOCKER_CODE_CREATE_BLOCKCHAIN = f"""
{DOCKER_CODE_PRELUDE}
docker_scripts.docker_create_blockchain()
docker_scripts.docker_add_block("BLOCK_CONTENT_STR".encode(), "BLOCK_TOPIC")
blockchain_data = docker_scripts.docker_get_blockchain_data()
docker_scripts.docker_terminate_blockchain()
print(blockchain_data)
"""
DOCKER_CODE_JOIN_BLOCKCHAIN = f"""
{DOCKER_CODE_PRELUDE}
docker_scripts.docker_load_blockchain("BC_ID", "APPDATA_CID")

docker_scripts.docker_add_block("BLOCK_CONTENT_STR".encode(), "BLOCK_TOPIC")
docker_scripts.docker_terminate_blockchain()
"""

DOCKER_CODE_CHECK_BLOCKS = f"""

{DOCKER_CODE_PRELUDE}
docker_scripts.docker_load_blockchain("BC_ID", "APPDATA_CID")
success = True
try:
    assert docker_scripts.docker_does_block_topic_exist("BLOCK_TOPIC_1")
    assert docker_scripts.docker_does_block_topic_exist("BLOCK_TOPIC_2")
    assert docker_scripts.docker_does_block_topic_exist("BLOCK_TOPIC_3")
except AssertionError:
    print("Not all expected blocks were found.")
    success = False
print("Blocks from all three topics exist.")

blockchain = docker_scripts.shared_data.blockchain
block_1= [b for b in blockchain.get_blocks() if "BLOCK_TOPIC_1" in b.topics][-1]
block_2= [b for b in blockchain.get_blocks() if "BLOCK_TOPIC_2" in b.topics][-1]
block_3= [b for b in blockchain.get_blocks() if "BLOCK_TOPIC_3" in b.topics][-1]

from datetime import timedelta
TIMEDELTA=timedelta(seconds={TIMEDELTA.total_seconds()})
try:
    assert block_1.creation_time - block_3.creation_time > 0.9*TIMEDELTA
    assert block_2.creation_time - block_1.creation_time > 0.9*TIMEDELTA
except AssertionError:
    print(block_1.creation_time)
    print(block_2.creation_time)
    print(block_3.creation_time)
    print("Temporal relationships between block timestamps not as expected.")
    success = False
docker_scripts.docker_terminate_blockchain()
print(int(success))
"""


def docker_create_blockchain(
    container: BrenthyDocker,
) -> BlockchainInfo:
    docker_code_create_blockchain = DOCKER_CODE_CREATE_BLOCKCHAIN
    docker_code_create_blockchain = docker_code_create_blockchain.replace(
        "BLOCK_CONTENT_STR", container.container.name
    )
    docker_code_create_blockchain = docker_code_create_blockchain.replace(
        "BLOCK_TOPIC", container.container.name
    )
    output = container.run_python_code(
        docker_code_create_blockchain, python_cmd=PYTHON_FAKETIME_CMD
    )

    last_line = output.split("\n")[-1].strip()
    try:
        result = json.loads(last_line)
        blockchain_id = result["blockchain_id"]
        appdata_cid = result["appdata_cid"]
        creation_time = string_to_time(result["creation_time"])
    except (json.JSONDecodeError, IndexError):
        print(output)
        raise Exception("Failed to create blockchain in docker container.")
    return BlockchainInfo(blockchain_id, appdata_cid, creation_time)


def docker_join_blockchain(
    container: BrenthyDocker, blockchain: BlockchainInfo
) -> None:
    docker_code_join_blockchain = DOCKER_CODE_JOIN_BLOCKCHAIN
    docker_code_join_blockchain = docker_code_join_blockchain.replace(
        "BC_ID", blockchain.blockchain_id
    )
    docker_code_join_blockchain = docker_code_join_blockchain.replace(
        "APPDATA_CID", blockchain.appdata_cid
    )
    docker_code_join_blockchain = docker_code_join_blockchain.replace(
        "BLOCK_CONTENT_STR", container.container.name
    )
    docker_code_join_blockchain = docker_code_join_blockchain.replace(
        "BLOCK_TOPIC", container.container.name
    )
    container.run_python_code(
        docker_code_join_blockchain, python_cmd=PYTHON_FAKETIME_CMD
    )


def docker_check_blocks(
    container: BrenthyDocker, blockchain: BlockchainInfo
) -> bool:
    docker_code_check_blocks = DOCKER_CODE_CHECK_BLOCKS
    docker_code_check_blocks = docker_code_check_blocks.replace(
        "BC_ID", blockchain.blockchain_id
    )
    docker_code_check_blocks = docker_code_check_blocks.replace(
        "APPDATA_CID", blockchain.appdata_cid
    )
    docker_code_check_blocks = docker_code_check_blocks.replace(
        "BLOCK_TOPIC", DOCKER_CONTAINER_NAME
    )
    output = container.run_python_code(
        docker_code_check_blocks, python_cmd=PYTHON_FAKETIME_CMD
    )
    last_line = output.split("\n")[-1].strip()
    match last_line:
        case "0":
            print(f"OUTPUT\n{output}")
            print(f"PYTHON_CODE\n{docker_code_check_blocks}")
            return False
        case "1":
            return True
        case _:
            print(output)
            raise Exception(
                "Unexpected output from checking blocks in docker container."
            )


def cleanup() -> None:
    """Ensure all resources used by tests are cleaned up."""
    if shared_data.brenthy_docker_1:
        shared_data.brenthy_docker_1.delete()
    if shared_data.brenthy_docker_2:
        shared_data.brenthy_docker_2.delete()
    if shared_data.brenthy_docker_3:
        shared_data.brenthy_docker_3.delete()
