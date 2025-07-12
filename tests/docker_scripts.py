
import os
import tempfile

import walytis_beta_api
from walytis_beta_api import (
    Blockchain,
)
from walytis_beta_tools._experimental.ipfs_interface import ipfs

BLOCKCHAIN_NAME = "TestingWalytisAppdata"
MESSAGE_1 = "Hello there!"
MESSAGE_2 = "Gday!"
MESSAGE_3 = "Hi!"

class SharedData:
    blockchain:Blockchain|None
shared_data=SharedData()

def docker_load_blockchain(bc_id: str, appdata_cid: str, ):
    download_tempdir = tempfile.mkdtemp()

    appdata_path = os.path.join(download_tempdir, "blockchain_data.zip")
    ipfs.files.download(appdata_cid, appdata_path)
    walytis_beta_api.join_blockchain_from_zip(
        bc_id, appdata_path, blockchain_name=BLOCKCHAIN_NAME
    )
    shared_data.blockchain = Blockchain(bc_id)


def docker_1_part_1(bc_id: str, appdata_cid: str, ):
    docker_load_blockchain(bc_id, appdata_cid)
    shared_data.blockchain.add_block(MESSAGE_2.encode())
    shared_data.blockchain.add_block(MESSAGE_2.encode())
    shared_data.blockchain.add_block(MESSAGE_2.encode())
    shared_data.blockchain.terminate()


def docker_2_part_1(bc_id: str, appdata_cid: str, ):
    docker_load_blockchain(bc_id, appdata_cid)
    shared_data.blockchain.add_block(MESSAGE_3.encode())
    shared_data.blockchain.add_block(MESSAGE_3.encode())
    shared_data.blockchain.add_block(MESSAGE_3.encode())
    shared_data.blockchain.terminate()


def docker_1_part_2():
    shared_data.blockchain = Blockchain(BLOCKCHAIN_NAME)
    print([block.content.decode()
          for block in shared_data.blockchain.get_blocks() if "genesis" not in block.topics])
    shared_data.blockchain.terminate()
