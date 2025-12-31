from brenthy_tools_beta import brenthy_api
import time
from dataclasses import dataclass
from conftest import get_rebuild_docker  # noqa

import pytest
from walytis_beta_tools._experimental.config import (
    WalytisTestModes,
    get_walytis_test_mode,
)
from emtest import are_we_in_docker

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
    if not are_we_in_docker():
        import run

        run.TRY_INSTALL = False
    import walytis_beta_api

    # print("PWB")
    if not are_we_in_docker():
        from brenthy_docker import BrenthyDocker
    from walytis_beta_api import Block, Blockchain

    # walytis_beta_api.log.PRINT_DEBUG = True


@dataclass
class SharedData:
    """Structure for storing objects created and shared between tests."""

    brenthy_dockers: list[BrenthyDocker]
    blockchains: list[Blockchain]
    blockchain: Blockchain | None
    num_blocks: int | None
    invitation: str | None
    created_block: Block | None
    WALYTIS_TEST_MODE: WalytisTestModes | None


shared_data = SharedData([], [], None, None, None, None, None)


def assert_brenthy_online(timeout: int = 2) -> None:
    """Check if Brenthy is reachable, raising an error if not."""
    brenthy_api.get_brenthy_version(timeout=timeout)


def run_walytis() -> None:
    """Test that we can run Brenthy-Core."""
    shared_data.WALYTIS_TEST_MODE = get_walytis_test_mode()
    match shared_data.WALYTIS_TEST_MODE:
        case WalytisTestModes.RUN_BRENTHY:
            # run.log.set_print_level("important")
            print("Running Brenthy...")
            run.run_brenthy()
            assert_brenthy_online()
        case WalytisTestModes.EMBEDDED:
            print("Running Walytis embedded...")
            import walytis_beta_embedded

            walytis_beta_embedded.run_blockchains()
            print("Running Walytis embedded.")
        case WalytisTestModes.USE_BRENTHY:
            print("Using Brenthy...")
            assert_brenthy_online()
        case 0:
            raise Exception("BUG in handling of WALYTIS_TEST_MODE!")


def stop_walytis() -> None:
    """Stop Brenthy-Core."""
    match shared_data.WALYTIS_TEST_MODE:
        case WalytisTestModes.RUN_BRENTHY:
            run.stop_brenthy()
        case WalytisTestModes.EMBEDDED:
            import walytis_beta_embedded

            walytis_beta_embedded.terminate()
        case WalytisTestModes.USE_BRENTHY:
            pass
        case 0:
            raise Exception("BUG in handling of WALYTIS_TEST_MODE!")


def delete_blockchains() -> None:
    """Delete all blockchains other than BrenthyUpdates."""
    for bc_id in walytis_beta_api.list_blockchain_ids():
        if not bc_id == "BrenthyUpdates":
            walytis_beta_api.delete_blockchain(bc_id)


def on_block_received(block: Block) -> None:
    """Eventhandler for newly created blocks on the test's blockchain."""
    global created_block
    created_block = block


def test_create_blockchain() -> None:
    """Test that we can create a Walytis blockchain."""
    shared_data.blockchain = walytis_beta_api.Blockchain.create(
        "TestingWalytis",
        app_name="BrenthyTester",
        block_received_handler=on_block_received,
    )

    success = isinstance(shared_data.blockchain, walytis_beta_api.Blockchain)
    assert success, "create_blockchain"

    time.sleep(2)


def test_add_block() -> None:
    """Test that we can add a block to the blockchain."""
    blockchain = shared_data.blockchain
    if not blockchain:
        pytest.skip("No blockchain created.")
    block = blockchain.add_block("Hello there!".encode())
    success = (
        block.short_id in blockchain._blocks.get_short_ids()
        and block.long_id in blockchain._blocks.get_long_ids()
        and blockchain.get_block(
            blockchain._blocks.get_short_ids()[-1]
        ).content.decode()
        == blockchain.get_block(
            blockchain._blocks.get_long_ids()[-1]
        ).content.decode()
        == "Hello there!"
    )
    assert success, "Blockchain.add_block"


def test_create_invitation() -> None:
    """Test that we can create an invitation for the blockchain."""
    blockchain = shared_data.blockchain
    if not blockchain:
        pytest.skip("No blockchain created.")
    shared_data.invitation = blockchain.create_invitation(one_time=False)
    success = (
        shared_data.invitation in blockchain.get_invitations(),
        "newly created invitation is not listed in blockchain's invitations",
    )
    assert success, "Blockchain.create_invitation"


def test_delete_blockchain() -> None:
    """Test that we can delete a blockchain."""
    blockchain = shared_data.blockchain
    if not blockchain:
        pytest.skip("No blockchain created.")
    blockchain.terminate()
    walytis_beta_api.delete_blockchain("TestingWalytis")
    success = (
        "TestingWalytis" not in walytis_beta_api.list_blockchain_names(),
        "failed to delete blockchain",
    )
    assert success, "delete_blockchain"


def test_list_blockchains() -> None:
    """Test that getting a list of blockchains ids and names works."""
    blockchain = shared_data.blockchain
    if not blockchain:
        pytest.skip("No blockchain created.")
    walytis_beta_api.list_blockchains()

    found = False
    for id, name in walytis_beta_api.list_blockchains():
        if id == blockchain.blockchain_id and name == blockchain.name:
            found = True
            break
    assert found, "walytis_beta_api.list_blockchains"


def test_list_blockchains_names_first() -> None:
    """Test that getting a list of blockchains works with the names first."""
    all_in_order = walytis_beta_api.list_blockchains(names_first=True) == [
        (name, id) for id, name in walytis_beta_api.list_blockchains()
    ]
    assert all_in_order, "walytis_beta_api.list_blockchains(names_first=true)"


def test_list_blockchain_ids() -> None:
    """Test that getting a list of blockchains ids."""
    blockchain = shared_data.blockchain
    if not blockchain:
        pytest.skip("No blockchain created.")
    all_in_order = (
        blockchain.blockchain_id in walytis_beta_api.list_blockchain_ids()
        and walytis_beta_api.list_blockchain_ids()
        == [id for id, name in walytis_beta_api.list_blockchains()]
    )
    assert all_in_order, "walytis_beta_api.list_blockchain_ids"


def test_list_blockchain_names() -> None:
    """Test that getting a list of blockchains names."""
    blockchain = shared_data.blockchain
    if not blockchain:
        pytest.skip("No blockchain created.")
    all_in_order = (
        blockchain.name in walytis_beta_api.list_blockchain_names()
        and walytis_beta_api.list_blockchain_names()
        == [name for id, name in walytis_beta_api.list_blockchains()]
    )
    assert all_in_order, "walytis_beta_api.list_blockchain_names"
