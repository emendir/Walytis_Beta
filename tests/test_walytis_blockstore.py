"""Test that Walytis' local block store works."""

# This import allows us to run this script with either pytest or python
from tqdm import tqdm
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

from walytis_beta_tools._experimental.config import (
    WalytisTestModes,
    get_walytis_test_mode,
)

NUM_BLOCKS_PER_INDEX_FILE = 100
if True:
    import run

    run.TRY_INSTALL = False
    import walytis_beta_api
    import walytis_beta
    from walytis_beta_tools.log import (
        logger_block_records,
        console_handler,
        file_handler,
    )
    import logging

    # logger_block_records.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG)

    # assert this field exists, and that we're reducing it
    assert (
        NUM_BLOCKS_PER_INDEX_FILE
        < walytis_beta.walytis_beta.Blockchain.max_num_blocks_per_file
    )
    walytis_beta.walytis_beta.Blockchain.max_num_blocks_per_file = (
        NUM_BLOCKS_PER_INDEX_FILE
    )


def setup_module():
    if not get_walytis_test_mode() == WalytisTestModes.EMBEDDED:
        print(
            f"Skipping this test, because WALYTIS_TEST_MODE is "
            f"{get_walytis_test_mode()}"
        )
        pytest.skip("Skipping whole test file", allow_module_level=True)


def test_preparations() -> None:
    """Get everything needed to run the tests ready."""

    testing_utils.run_walytis()

    if "TestingWalytis" in walytis_beta_api.list_blockchain_names():
        walytis_beta_api.delete_blockchain("TestingWalytis")
    print("Finished preparations...")


def cleanup(request: pytest.FixtureRequest | None = None) -> None:
    """Clean up after running tests with PyTest."""
    # _testing_utils.terminate()

    testing_utils.stop_walytis()


def test_create_blockchain() -> None:
    """Test that we can create a Walytis blockchain."""
    testing_utils.shared_data.blockchain = walytis_beta_api.Blockchain.create(
        "TestingWalytis",
        app_name="WalytisTester",
    )


BLOCK_SIZE_BYTES = 100000
TOPIC_SIZE_BYTES = 1000
N_BLOCKS = 300


def test_add_blocks() -> None:
    """Test that we can add a block to the blockchain."""
    blockchain = testing_utils.shared_data.blockchain

    for i in tqdm(range(N_BLOCKS)):
        blockchain.add_block(
            bytearray([0]) * BLOCK_SIZE_BYTES,
            topics=[(bytearray([64]) * TOPIC_SIZE_BYTES).decode()],
        )
    testing_utils.shared_data.num_blocks = blockchain.get_num_blocks()


def test_reload_blockchain() -> None:
    testing_utils.stop_walytis()
    testing_utils.run_walytis()
    testing_utils.shared_data.blockchain = walytis_beta_api.Blockchain(
        "TestingWalytis",
        app_name="WalytisTester",
    )
    blockchain = testing_utils.shared_data.blockchain
    assert testing_utils.shared_data.num_blocks == blockchain.get_num_blocks()


def test_read_blockchain() -> None:
    blockchain = testing_utils.shared_data.blockchain
    for block in tqdm(blockchain.get_blocks()):
        _ = block.content


def test_delete_blockchain() -> None:
    """Test that we can delete a blockchain."""
    testing_utils.test_delete_blockchain()


def test_threads_cleanup() -> None:
    """Test that no threads are left running."""
    shared_data.blockchain.terminate()
    testing_utils.stop_walytis()
    assert await_thread_cleanup(timeout=5)
    cleanup()
