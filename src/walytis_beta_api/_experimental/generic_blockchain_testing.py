"""Testing functions to check GenericBlockchain implementations' integrity."""
import string
import random
from random import randint
from walytis_beta_api._experimental.generic_blockchain import GenericBlockchain, GenericBlock
from walytis_beta_api import Blockchain

# set the range of topic-lengths to test when adding blocks,
# from 0 to this value
N_BLOCK_TOPICS_TO_TEST = 4




def _generate_random_bytes():
    data_length = randint(1, 100)
    data = bytearray([0]) * data_length
    for i in range(data_length):
        data[i] = randint(0, 255)
    return data


def _generate_random_string(length=8) -> str:
    # Choose from lowercase and uppercase letters
    # letters = string.ascii_letters  # This is a-zA-Z
    letters = string.printable  # all printable characters
    return ''.join(random.choice(letters) for _ in range(length))


def _test_add_block(blockchain: GenericBlockchain, n_topics: int) -> GenericBlock:
    content = _generate_random_bytes()

    topics = [_generate_random_string(randint(1, 5)) for i in range(n_topics)]
    block_1 = blockchain.add_block(content, topics)

    assert blockchain.get_block_ids()[-1] == block_1.long_id, f"NT: {n_topics} - Blockchain.get_block_ids"
    assert blockchain.get_block(-1).short_id == block_1.short_id, f"NT: {n_topics} - Blockchain.get_block"
    assert blockchain.get_block(-1).content == block_1.content, f"NT: {n_topics} - Block.content"
    assert blockchain.get_block(-1).topics == block_1.topics, f"NT: {n_topics} - Block.topics"
    return block_1


def run_generic_blockchain_test(blockchain_type, **kwargs) -> GenericBlockchain:
    if not issubclass(blockchain_type, GenericBlockchain):
        raise ValueError(
            "The parameter `blockchain_type` must be a class that inherits "
            "`walytis_beta_api._experimental.generic_blockchain.GenericBlockchain`"
        )
    blockchain: GenericBlockchain = blockchain_type(**kwargs)
    # assert blockchain.get_num_blocks() == 0, "Provided blockchain shouldn't expose blocks yet"
    blocks = [
        _test_add_block(blockchain, i) for i in range(N_BLOCK_TOPICS_TO_TEST)
    ]

    # check that the last few block IDs are the created blocks
    success = True
    for i, block in enumerate(blocks):
        expected_index = i - len(blocks)
        if blockchain.get_block_ids()[expected_index] != block.long_id:
            success = False

    assert success, "No hidden blocks exposed"
    long_block_ids = blockchain.get_block_ids()
    blockchain.terminate()
    blockchain: GenericBlockchain = blockchain_type(**kwargs)
    assert long_block_ids == blockchain.get_block_ids(), "block_ids correctly reloaded"

    return blockchain

