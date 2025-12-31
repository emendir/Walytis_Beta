import json
import os
import tempfile
from brenthy_tools_beta.utils import time_to_string, string_to_time
import walytis_beta_api
from walytis_beta_api import (
    Blockchain,
)
from walytis_beta_tools._experimental.ipfs_interface import ipfs

MESSAGE_1 = "Hello there!"
MESSAGE_2 = "Gday!"
MESSAGE_3 = "Hi!"


class SharedData:
    blockchain: Blockchain | None


shared_data = SharedData()


def docker_create_blockchain():
    shared_data.blockchain = Blockchain.create()
    appdata_path = shared_data.blockchain.get_blockchain_data()
    assert os.path.isfile(appdata_path), "Got blockchain appdata."
    shared_data.appdata_cid = ipfs.files.publish(appdata_path)


def docker_get_blockchain_data() -> str:
    return json.dumps(
        {
            "blockchain_id": shared_data.blockchain.blockchain_id,
            "appdata_cid": shared_data.appdata_cid,
            "creation_time": time_to_string(
                shared_data.blockchain.get_block(0).creation_time
            ),
        }
    )


def docker_add_block(content: bytes, topic: str):
    shared_data.blockchain.add_block(content, topic)


def docker_does_block_topic_exist(topic: str):
    for block in shared_data.blockchain.get_blocks():
        if topic in block.topics:
            return True
    return False


def docker_terminate_blockchain():
    shared_data.blockchain.terminate()


def docker_load_blockchain(
    bc_id: str,
    appdata_cid: str,
):
    if bc_id not in walytis_beta_api.list_blockchain_ids():
        try:
            download_tempdir = tempfile.mkdtemp()

            appdata_path = os.path.join(
                download_tempdir, "blockchain_data.zip"
            )
            ipfs.files.download(appdata_cid, appdata_path)
            walytis_beta_api.join_blockchain_from_zip(bc_id, appdata_path)
        except walytis_beta_api.BlockchainAlreadyExistsError:
            pass
    shared_data.blockchain = Blockchain(bc_id)


def docker_1_part_1(
    bc_id: str,
    appdata_cid: str,
):
    docker_load_blockchain(bc_id, appdata_cid)
    shared_data.blockchain.add_block(MESSAGE_2.encode())
    shared_data.blockchain.add_block(MESSAGE_2.encode())
    shared_data.blockchain.add_block(MESSAGE_2.encode())
    shared_data.blockchain.terminate()


def docker_2_part_1(
    bc_id: str,
    appdata_cid: str,
):
    docker_load_blockchain(bc_id, appdata_cid)
    shared_data.blockchain.add_block(MESSAGE_3.encode())
    shared_data.blockchain.add_block(MESSAGE_3.encode())
    shared_data.blockchain.add_block(MESSAGE_3.encode())
    shared_data.blockchain.terminate()


def docker_1_part_2(
    bc_id: str,
    appdata_cid: str,
):
    docker_load_blockchain(bc_id, appdata_cid)
    print(
        [
            block.content.decode()
            for block in shared_data.blockchain.get_blocks()
            if "genesis" not in block.topics
        ]
    )
    shared_data.blockchain.terminate()
