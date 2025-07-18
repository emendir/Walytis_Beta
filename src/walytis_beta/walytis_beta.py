"""Core Walytis blockchain functionality."""
# pylint: disable=import-error

import copy
import json
import os
import shutil
import threading
import time
import traceback
from datetime import datetime
from random import randint, seed
from threading import Lock, Thread
from time import sleep

from brenthy_tools_beta.utils import (
    are_elements_unique,
    bytes_to_string,
    decode_timestamp,
    from_b255_no_0s,
    function_name,
)
from brenthy_tools_beta.version_utils import decode_version, is_version_greater
from ecies.utils import generate_key
from walytis_beta_tools.block_model import (
    decode_long_id,
    decode_short_id,
    short_from_long_id,
)
from walytis_beta_tools.exceptions import NotSupposedToHappenError

# import api_terminal as AppCom
from walytis_beta_tools.log import logger
from walytis_beta_tools.versions import WALYTIS_BETA_CORE_VERSION

from . import walytis_beta_api_terminal
from .block_networking import (
    Block,
    IpfsCidExistsError,
)
from .block_records import BlockRecords
from .exceptions import BlockchainNotInitialised, BlockchainTerminatedError
from .networking import Networking, ipfs
from .walytis_beta_appdata import (
    BlockchainAppdata,
    create_temp_dir,
    get_walytis_appdata_dir,
)

# a variable with this blockchain's name so that we don't missspell it
WALYTIS_BETA = "Walytis_Beta"

# from brenthy_tools_beta.utils import string_to_bytes, bytes_to_string
N_GENESIS_BLOCKS = 5
# how many blocks we load at startup
# for use as potential parent blocks for blocks we create
N_STARTUP_ENDBLOCKS = 10

JOIN_COMMS_TIMEOUT_S = 10
JOIN_COMMS_FILE_TIMEOUT_S = 30


class Blockchain(BlockchainAppdata, BlockRecords, Networking):
    """The Walytis_Beta blockchain.

    Brenthy can run any number of blockchain types.
    This is the blockchain whose invention lead to the development of Brenthy.

    OOOOOOOOOO
    OOἅλυσιςOO
    OOOOOOOOOO
    """

    blocks_finder_thread_cycle_duration_s = 5
    create_block_lock: Lock
    genesis: bool

    def __init__(self, id: str = "", name: str = ""):
        """Load an existing blockchain, or creat a new one.

        Loads an existing blockchain from appdata if `id` is specified,
        otherwise it creates a new Blockchain.
        """
        self.name = name
        # list of parent short_ids
        self.current_endblocks: list[bytearray] = []
        self.unconfirmed_blocks: list[Block] = []
        self.blocks_to_find: list[bytearray] = []  # list(short_id)

        self.invitations = []

        self.create_block_lock = Lock()  # ensures sequential block creation
        self.endblocks_lock = Lock()  # for accessing current_endblocks
        # lock for accessing unconfirmed_blocks and blocks_to_find
        self.blocks_to_confirm_lock = Lock()
        self._terminate = False  # flag when we're shutting down
        self._genesis = False
        self.ipfs_peer_id = ipfs.peer_id

        if not id:
            # Create new blockchain:
            self.blockchain_id = ""
            self.__birth()
        else:
            # Using existing blockchain:
            if not isinstance(id, str):
                error_message = (
                    f"Parameter id must be of type str, not {type(id)}"
                )
                logger.error(error_message)
                raise TypeError(error_message)
            self.blockchain_id = id
            self.appdata_dir = os.path.join(
                get_walytis_appdata_dir(), self.blockchain_id
            )
            BlockchainAppdata.__init__(self)
            BlockRecords.__init__(self)
            Networking.__init__(self)
            if not self.name:
                self.name = self.blockchain_id[:14]

            # create a list of blocks to use as parents for block creation
            self.current_endblocks = self.remove_ancestors(
                [
                    short_from_long_id(long_id)
                    for long_id in self.load_latest_block_ids(
                        N_STARTUP_ENDBLOCKS
                    )
                ]
            )

            self.listen_for_blocks()
        self._blocks_finder_thread = threading.Thread(
            target=self.blocks_finder_thread,
            args=(),
            name="BlocksFinderThread",
        )
        self._blocks_finder_thread.start()

        self.conv_lis = ipfs.listen_for_conversations(
            f"{self.blockchain_id}: JoinRequest", self.on_join_request_received
        )

        # run the loop that asks othe rnodes for their latest blocks
        # when the block publishing pubsub channel gets too quiet
        self.block_requester_thread = threading.Thread(
            target=self.leaf_blocks_broadcaster,
            args=(),
            name="BlockRequesterThread",
        )
        self.block_requester_thread.start()

    def __birth(self) -> None:
        """Perform the blockchain creation procedure."""
        self._genesis = True
        self.check_alive()  # ensure this Blockchain object isn't shutting down

        # initialise the part of the uninitialised BlockRecords which we need
        self.block_id_cache = []

        seed(datetime.now().microsecond)
        genesis_blocks = []

        logger.info("Generating genesis blocks...")
        self.number_of_known_ids = 0
        for b in range(N_GENESIS_BLOCKS):
            block = self.create_block(
                "Hello World, new blockchain getting born!".encode()
                + bytearray([randint(0, 255) for a in range(1000)]),
            )
            genesis_blocks.append(block)
            self._genesis_block_id = genesis_blocks[0].long_id
        self.__born(genesis_blocks[0])
        self._genesis_block_id = genesis_blocks[0].long_id
        logger.info("Storing genesis blocks...")
        self.current_endblocks = []
        for block in genesis_blocks:
            self.download_and_process_block(block.short_id)

        # self.number_of_known_ids = len(genesis_blocks)

        self._genesis = False

        for block in genesis_blocks:
            self.publish_new_block(block)
        logger.info("Finished processing Genesis blocks!")
        self.listen_for_blocks()

    def __born(self, genesis_block: Block) -> None:
        """Perform operation needed as soon as the genesis block is created."""
        # skip if this function has already been executed by thge genesis block
        self.check_alive()  # ensure this Blockchain object isn't shutting down

        self.blockchain_id = genesis_block.ipfs_cid
        if not self.name:
            self.name = self.blockchain_id[:14]
        self.appdata_dir = os.path.join(
            get_walytis_appdata_dir(), self.blockchain_id
        )

        if os.path.exists(self.appdata_dir):
            backup_path = self.appdata_dir + "_BACKUP"
            logger.error(
                "This shouldn't happen but it has: Appdata path "
                f"already exists for blockchain {self.name}. "
                f"Moving it to {backup_path}."
            )
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
                logger.error(
                    "This shouldn't happen but it has: Backup "
                    "path for appdata already exists! Overwriting :("
                )
            shutil.move(self.appdata_dir, backup_path)

        os.makedirs(self.appdata_dir)
        BlockchainAppdata.__init__(self)
        BlockRecords.__init__(self)
        Networking.__init__(self)

    def create_block(
        self, content: bytearray | bytes, topics: list[str] = []
    ) -> Block:
        """Create a new block, adding it to this blockchain.

        Args:
            content: the content which you want to store in this block
            topics: optional labels for this block to aid in the user's
                        sorting of blocks
        """
        self.check_alive()  # ensure this Blockchain object isn't shutting down

        if isinstance(topics, str):
            topics = [topics]
        # if we're creating a genesis block
        if self._genesis:
            topics = ["genesis"]
        elif "genesis" in topics:
            error_message = (
                "I won't create a block with topic 'genesis'"
            )
            logger.error(error_message)
            raise ValueError(error_message)

        if not self.blockchain_id:
            # safety check
            if not self._genesis:
                error_message = (
                    "CreateBlock: Blockchain id is not yet "
                    "defined and this block is not marked as a genesis block"
                )
                logger.error(error_message)
                raise BlockchainNotInitialised()
        elif self.blockchain_id not in topics:
            topics.append(self.blockchain_id)

        logger.info(f"{self.name}:  Creating block for {topics}...")

        self.create_block_lock.acquire()
        block_blockchain_version = WALYTIS_BETA_CORE_VERSION
        block_content = content
        block_creation_time = datetime.utcnow()

        block_parents = []
        # Adding parent blocks
        with self.endblocks_lock:
            block_parents = self.remove_ancestors(self.current_endblocks)
            self.current_endblocks = []  # clear current_endblocks

        # if parents is only one block, add genesis block
        if len(block_parents) == 1:
            block_parents.append(short_from_long_id(self.get_genesis_block()))
        # sort parent blocks
        block_parents.sort()
        # ensure that all parent blocks have older timestamps than this block
        if [
            prnt_id
            for prnt_id in block_parents
            if decode_short_id(prnt_id)["creation_time"] > block_creation_time
        ]:
            self.create_block_lock.release()

            error_message = (
                "walytis_beta.Blockchain.create_block: Parent block's creation"
                " time is greater than this block's creation time "
                f"{block_creation_time}. This is a bug because it should have "
                "been checked before."
            )
            logger.error(error_message)
            raise NotSupposedToHappenError(error_message)

        block_creator_id = self.ipfs_peer_id.encode("utf-8")
        block_topics = topics
        block_content_length = len(block_content)
        block_n_parents = len(block_parents)

        block = Block.from_metadata(
            creator_id=block_creator_id,
            creation_time=block_creation_time,
            topics=block_topics,
            content_length=block_content_length,
            content=bytearray(content),
            n_parents=block_n_parents,
            parents=block_parents,
            blockchain_version=block_blockchain_version,

            ipfs_cid="",
            content_hash_algorithm="",
            content_hash=bytearray(),
            parents_hash_algorithm="",
            parents_hash=bytearray(),
            file_data=bytearray(),
        )

        def finish_and_publish_block() -> None:
            block._creation_time = datetime.utcnow()
            block.generate_content_hash()
            block.generate_parents_hash()
            block.generate_file_data()

            block.publish_and_generate_id(
                self.blockchain_id, skip_pubsub=self._genesis
            )

        # Try building and publishing the block.
        # If another file on IPFS already has the block's predicted CID,
        # retry building block with new timestamp.
        published = False
        while not published:
            try:
                finish_and_publish_block()
                published = True
            except IpfsCidExistsError:
                logger.warning(
                    "walytis_beta.create_block: retrying block creation with "
                    "new timestamp"
                )

        logger.info(f"{self.name}:  Finished building block.")
        if self._genesis:
            # logger.info(f"{self.name}:  Genesis block!")
            # manually cache block because BlockRecords isn't initialised
            self.cache_block(block.long_id)
        else:
            self.check_new_block(block)

        with self.endblocks_lock:
            if block.short_id not in self.current_endblocks:
                # add block to current_endblocks, remove ancestors
                self.current_endblocks = self.remove_ancestors(
                    self.current_endblocks + [block.short_id]
                )
        logger.info(
            f"{self.name}:  Finished adding new block to the blockchain.")

        # DEBUG
        long_id = decode_long_id(block.long_id)

        if block.ipfs_cid != long_id["ipfs_cid"]:
            logger.warning(
                f"{self.name}:  MISMATCH ipfs_cid "
                + str(block.ipfs_cid)
                + " != "
                + str(long_id["ipfs_cid"])
            )
        if block.creator_id != long_id["creator_id"]:
            logger.warning(
                f"{self.name}:  MISMATCH creator_id "
                + str(block.creator_id)
                + " != "
                + str(long_id["creator_id"])
            )
        if block.creation_time != long_id["creation_time"]:
            logger.warning(
                f"{self.name}:  MISMATCH creation_time "
                + str(block.creation_time)
                + " != "
                + str(long_id["creation_time"])
            )
        if block.topics != long_id["topics"]:
            logger.warning(
                f"{self.name}:  MISMATCH topics "
                + str(block.topics)
                + " != "
                + str(long_id["topics"])
            )
        if block._content_length != long_id["content_length"]:
            logger.warning(
                f"{self.name}:  MISMATCH content_length "
                + str(block._content_length)
                + " != "
                + str(long_id["content_length"])
            )
        if block._n_parents != long_id["n_parents"]:
            logger.warning(
                f"{self.name}:  MISMATCH n_parents "
                + str(block._n_parents)
                + " != "
                + str(long_id["n_parents"])
            )
        if block._content_hash_algorithm != long_id["content_hash_algorithm"]:
            logger.warning(
                f"{self.name}:  MISMATCH content_hash_algorithm "
                + str(block._content_hash_algorithm)
                + " != "
                + str(long_id["content_hash_algorithm"])
            )

        if block._content_hash != long_id["content_hash"]:
            logger.warning(
                f"{self.name}:  MISMATCH hash "
                + str(block._content_hash)
                + " != "
                + str(long_id["content_hash"])
            )
        if block._parents_hash != long_id["parents_hash"]:
            logger.warning(
                f"{self.name}:  MISMATCH hash "
                + str(block._parents_hash)
                + " != "
                + str(long_id["parents_hash"])
            )
        if block.parents != long_id["parents"] and (
            len(block.parents) > 0 and len(long_id["parents"]) > 0
        ):
            logger.warning(
                f"{self.name}:  MISMATCH parents"
                + str(block.parents)
                + " != "
                + str(long_id[5])
            )

        self.create_block_lock.release()

        if not self._genesis:
            # inform applications about the new block
            self.publish_new_block(block)

        return block

    def publish_new_block(self, block: Block):
        walytis_beta_api_terminal.publish_event(
            self.blockchain_id,
            message={"block_id": bytes_to_string(block.short_id)},
            topics="NewBlocks",
        )

    def new_block_published(self, short_id: bytearray) -> None:
        """Eventhandler for when a notification of a new block is received."""
        self.check_alive()  # ensure this Blockchain object isn't shutting down

        logger.info(f"{self.name}:  Received new block.")
        self.download_and_process_block(short_id)

    def download_and_process_block(self, long_id: bytearray, live=True) -> Block | None:
        """Download a new block, add it to our block history if it is ok."""
        self.check_alive()  # ensure this Blockchain object isn't shutting down

        # when blockchain is being born, wait for genesis blocks to be created,
        # Blockchain ID determined, and all systems to start up
        self.block_record_initialised.wait()

        # get block datafile from IPFS
        short_id = short_from_long_id(long_id)
        try:
            ipfs_cid = decode_short_id(short_id)["ipfs_cid"]
            # get block datafile from IPFS
            block_data = ipfs.files.read(ipfs_cid)
        except Exception as error:
            logger.error(error)

            logger.error(
                f"{self.name}: Received data but failed to "
                + f"find block.\n{self.name}\nBlock ID: \n{short_id}"
            )
            return None
        block = None
        try:
            block = self.read_block(block_data, ipfs_cid, live=live)
        except Exception as error:  # if file data seems corrupt
            logger.error(error)
            logger.important(
                f"{self.name}:  Failed to build block. Removing block-file "
                "from IPFS storage"
            )
            # remove block-file from IPFS storage
            ipfs.files.remove(ipfs_cid)
        if not block:
            logger.important(f"{self.name}:  Failed to load and add block.")

            return None
        logger.info(f"{self.name}:  Block was processed.")
        while short_id[-1] == 0:
            short_id = short_id[:-1]
        if bytearray(block.short_id) != bytearray(short_id):  # suspicious
            message = (
                f"{self.name}: The decoded block's ID is not the "
                + "same as the one we are looking for.\n"
            )
            message += f"Looking for: {bytearray(short_id)}\n"
            message += f"Generated from BlockData: {block.short_id}\n"
            logger.warning(message)

            return None

        # Doing all the necessary management
        # when a new block has been decoded and confirmed:

        self.on_block_confirmed(block)

        logger.info(f"{self.name}:  Finished processing new block.")
        return block

    def on_block_confirmed(self, block: Block):
        # if the block is not already known to us
        if not self.check_new_block(block):
            with self.endblocks_lock:
                if block.short_id not in self.current_endblocks:
                    # add block to current_endblocks, remove ancestors
                    self.current_endblocks = self.remove_ancestors(
                        self.current_endblocks + [block.short_id]
                    )

            logger.info(
                f"{self.name}:  sending received block to " + "applications..."
            )

            if not self._genesis:
                # inform applications about the new block
                self.publish_new_block(block)

    def read_block(
        self, block_data: bytearray | bytes, ipfs_cid: str, live: bool = True
    ) -> Block | None:
        """Read a block file, returning a Block object if it is valid.

        Reads a block data file, decoding it, extracting its metadata.
        Unless the `live` parameter is set to False, this block's validity in
        the context of this blockchain will be checked, is registered
        in this blockchain's block archive etc.

        Args:
            block_data (bytearray): the block-file's data of the block to read.
            ipfs_cid (str): the IPFS CID the published block-file had
            live (bool): if True, this block processes of handling a new block
                in the context of a running blockchain will be performed, such
                as will have its parents checked, adding the block to the list
                of unconfirmed blocks, adding this block's unknown parents to
                self.blocks_to_find etc.

        Returns:
            Block | None: A block object, compiled from reading the block data.
                If block data is invalid, or live==true and the block hasn't
                been confirmed, None is returned.
        """
        self.check_alive()  # ensure this Blockchain object isn't shutting down

        if [
            b
            for b in self.unconfirmed_blocks
            if b.ipfs_cid == ipfs_cid
        ]:
            logger.debug(
                f"{self.name}:  read_block: this block is already in our "
                "unconfirmed_blocks list "
            )
            return None
        # if self.is_block_cid_known(ipfs_cid):
        #     logger.debug(
        #         f"{self.name}:  read_block: we already know this block."
        #     )
        #     return self.load_block_from_cid(ipfs_cid)
        logger.info(
            f"{self.name}:  read_block: Decoding block "
            f"{'(live)' if live else '(not live)'}"
        )

        # making a copy of the data to work with
        data = bytearray(block_data)

        blockchain_version = decode_version(
            data[: data.index(bytearray([0, 0]))]
        )

        # If the block has a greater major version than the Walytis_Beta
        # version we are, we can't process this block, so return
        if is_version_greater(
            blockchain_version[:-2], WALYTIS_BETA_CORE_VERSION[:-2]
        ):
            logger.error(
                "Walytis_Beta.read_block: can't process block with newer "
                f"Walytis_Beta version. Block: {blockchain_version}"
                f"Us: {WALYTIS_BETA_CORE_VERSION}"
            )
            return None

        # extract metadata block (separated from content by [0,0,0,0,0])
        # and splt it into is subcomponents separated by [0,0]
        content_separator = data.index(bytearray([0, 0, 0, 0, 0]))
        blockfile_header = data[:content_separator].split(
            bytearray([0, 0, 0, 0])
        )
        metadata = blockfile_header[0].split(bytearray([0, 0]))
        # logger.important(data)
        # logger.important(blockfile_header)
        # logger.important(metadata)
        if len(blockfile_header) > 1:
            parents = blockfile_header[1].split(bytearray([0, 0, 0]))
        else:
            parents = []
            # logger.important("Genesis block")
        # content sits between metadata and block_hash
        content = data[content_separator + 5:]

        # # duplicate
        # blockchain_version = decode_version(metadata[0])
        creator_id = metadata[1]
        creation_time = decode_timestamp(metadata[2])

        topics = [
            topic.decode() for topic in metadata[3].split(bytearray([0]))
        ]
        content_length = from_b255_no_0s(metadata[4])
        content_hash_algorithm = metadata[5].decode()
        content_hash = metadata[6]

        n_parents = from_b255_no_0s(metadata[7])
        parents_hash_algorithm = metadata[8].decode()
        parents_hash = metadata[9]

        # Check block rules that can and need only be checked in the context
        # of a running blockchain:
        if live:
            # Check block's parents
            # logger.info(f"{self.name}:  read_block: Checking parents...")
            result = self.check_blocks_parents(parents)
            logger.info(f"{self.name}:  read_block: Checked parents: {result}")
            if result == "invalid":
                logger.warning(
                    f"{self.name}: blockchain_manager.Readblock: "
                    "self.check_blocks_parents returned 'invalid'.  "
                    f"Topics: {topics}"
                )
                return None
            elif result == "confirmed":
                parents_confirmed = True
            elif result == "unconfirmed":
                parents_confirmed = False
            else:
                logger.warning(
                    "BUG - Blockchain.read_block: There is a bug in "
                    "blockchain_manager.self.check_blocks_parents, it "
                    "didn't return a return code"
                )
                return None
            if len(parents) == 0:
                logger.info(f"{self.name}:  Genesis block!")

            # Check block's timestamp is in the past
            if creation_time > datetime.now():
                logger.warning(
                    (
                        "Received a block with a timestamp in the future: "
                        f"{creation_time}. This is most likely due to "
                        "badly synchronised node clocks, but could also be "
                        "due to an ill-informed forgery attempt."
                    )
                )
                return None

        # creating a new block object from the decoded block data
        block = Block.from_metadata(

            blockchain_version=blockchain_version,
            creator_id=creator_id,
            creation_time=creation_time,
            topics=topics,
            content_length=content_length,
            content_hash_algorithm=content_hash_algorithm,
            content_hash=content_hash,
            content=content,
            n_parents=n_parents,
            parents_hash_algorithm=parents_hash_algorithm,
            parents_hash=parents_hash,
            parents=parents,
            ipfs_cid=ipfs_cid,
            file_data=bytearray(block_data),
        )

        block.generate_id()

        # making sure the block's block_hash is correct
        if not block.check_integrity():
            logger.warning(
                f"{self.name}:  The received block is not valid!Removing "
                "block-file from IPFS storage"
            )
            # remove block-file from IPFS storage
            ipfs.files.remove(ipfs_cid)
            return None

        if self:
            logger.info(f"{self.name}:  Block from {topics} decoded.")

        if not live:
            return block

        if not parents_confirmed:
            self.blocks_to_confirm_lock.acquire()
            # add block to unconfirmed_blocks if it isn't already there
            if not [
                b
                for b in self.unconfirmed_blocks
                if b.short_id == block.short_id
            ]:
                self.unconfirmed_blocks.append(block)
            self.blocks_to_confirm_lock.release()
            logger.important(
                f"{self.name}:  Block's parents not all confirmed, added to "
                f"blocks_to_confirm."
            )
            # logger.important((
            #     f"Unconfirmed blocks: {len(self.unconfirmed_blocks)}\n\n"+
            #     "\n\n".join([
            #         f"{block.long_id}"
            #          for block in self.unconfirmed_blocks
            #      ])
            #      +"\n\n"
            # ))
            return None
        else:  # parents_confirmed == True
            logger.info(f"{self.name}:  All in order with the new block.")
            self.blocks_to_confirm_lock.acquire()
            _update_btf = block.short_id in self.blocks_to_find
            if _update_btf:
                self.blocks_to_find.remove(block.short_id)
            self.blocks_to_confirm_lock.release()
            if _update_btf:
                self.check_on_unconfirmed_blocks()

            return block

    def check_blocks_parents(
        self, parents: list[bytearray], got_unconf_blocks_lock: bool = False
    ) -> str:
        """Check if a block has a valid parent list."""
        self.check_alive()  # ensure this Blockchain object isn't shutting down

        # copy parents list because we'll need to edit it in one of the checks
        parents = copy.deepcopy(parents)
        genesis_short_id = None
        if self._genesis_block_id:
            genesis_short_id = short_from_long_id(self._genesis_block_id)

        # Check special case first two genesis blocks:

        # if the blockchain is being born
        if self._genesis:
            # if this is the first genesis block:
            if len(parents) == self.number_of_known_ids == 0:
                # if the new block has as many parents
                # as the number of blocks known to me
                return "confirmed"

            # If this is the second genesis block
            if (
                self.number_of_known_ids == 1
                and parents == [genesis_short_id] * 2
            ):
                return "confirmed"

        # Ensure there aren't duplicates in parents:
        if not are_elements_unique(parents):
            logger.warning(
                f"{self.name}:  Block has repeated parents. "
                "Block not accepted."
            )
            return "invalid"

        # Ensure there are at least two parents:
        if len(parents) < 2:
            logger.warning(f"Block has {len(parents)} parents")
            return "invalid"

        if not genesis_short_id:
            genesis_short_id = short_from_long_id(self.get_genesis_block())

        # Checking if we know all of the parent blocks
        known_parents_count = 0
        for parent in parents:
            if self.is_block_known(parent):
                known_parents_count += 1
            else:  # parent is not known
                # append parent to blocks_to_find (if it isn't already)
                if not got_unconf_blocks_lock:
                    logger.info("Acquiring lock...")
                    self.blocks_to_confirm_lock.acquire()
                if parent not in self.blocks_to_find:
                    self.blocks_to_find.append(parent)
                if not got_unconf_blocks_lock:
                    self.blocks_to_confirm_lock.release()
                    logger.info("Released lock.")
        if known_parents_count < len(parents):
            return "unconfirmed"

        # ensure no parents are ancestors of each other
        # remove genesis parent if block has only one direct parent
        if len(parents) == 2 and genesis_short_id in parents:
            parents.remove(genesis_short_id)
        if len(parents) != len(self.remove_ancestors(parents)):
            logger.warning(
                (
                    f"{self.name}:  Some of the block's parents are "
                    "ancestors of each other."
                )
            )
            return "invalid"

        return "confirmed"

    def remove_ancestors(
        self, blocks: list[bytearray], short_ids: bool = True
    ) -> list[bytearray]:
        """Given a list of blocks, remove any which is an ancestors of another.

        Args:
            blocks (list): list of Block objects or block IDs
            short_ids (bool): if the provided block IDs are short not long
        Returns:
            list: long IDs of blocks
        """
        from .block_ancestry import remove_ancestors

        long_ids = remove_ancestors(self, blocks)
        if short_ids:
            return [short_from_long_id(long_id) for long_id in long_ids]
        else:
            return long_ids

    def check_on_unconfirmed_blocks(self) -> None:
        """Check if unconfirmed blocks can be validated now."""
        self.check_alive()  # ensure this Blockchain object isn't shutting down

        num_confirmed = 0
        self.blocks_to_confirm_lock.acquire()
        for block in self.unconfirmed_blocks:
            result = self.check_blocks_parents(block.parents, True)
            if result == "invalid":
                self.unconfirmed_blocks.remove(block)
            elif result == "confirmed":
                self.unconfirmed_blocks.remove(block)
                if block.short_id in self.blocks_to_find:
                    self.blocks_to_find.remove(block.short_id)
                logger.info("Confirmed a previously unconfirmed block!")
                self.on_block_confirmed(block)
                num_confirmed += 1
                break
        self.blocks_to_confirm_lock.release()
        if num_confirmed > 0:
            self.check_on_unconfirmed_blocks()
        # logger.info(
        #     f"{self.name} Unconfirmed Blocks: {len(self.unconfirmed_blocks)}"
        # )
        # logger.info(f"{self.name} Blocks to Find: {len(self.blocks_to_find)}")

    def look_for_blocks_to_find(self) -> None:
        """Try to get blocks we have heard about but don't have."""
        self.check_alive()  # ensure this Blockchain object isn't shutting down

        for blocks_id in self.blocks_to_find:
            self.download_and_process_block(blocks_id)

    def blocks_finder_thread(self) -> None:
        """Try to get blocks we have heard about but don't have."""
        self.check_alive()  # ensure this Blockchain object isn't shutting down

        while not self._terminate:
            self.look_for_blocks_to_find()
            self.check_on_unconfirmed_blocks()
            time.sleep(self.blocks_finder_thread_cycle_duration_s)

    def create_invitation(
        self, one_time: bool = True, shared: bool = False
    ) -> str:
        """Create a code which another node can use to join this blockchain.

        Args:
            one_time (bool): whether or not the invitation should be discarded
                    once a peer uses it to join the blockchain
            shared (bool): whether or not the invitation should be transferred
                    to other peers when they join the blockchain
                    (implies one_time=False)

        Returns:
            dict: the invitation
        """
        self.check_alive()  # ensure this Blockchain object isn't shutting down

        # 'one_time == True' makes no sense if shared == True
        if shared:
            one_time = False
        private_key = generate_key()

        data = {
            "blockchain_id": self.blockchain_id,
            "peers": [self.ipfs_peer_id],
            "key": private_key.public_key.format(False).hex(),
            "one_time": one_time,
            "shared": shared,
        }
        invitation = json.dumps(data)
        self.invitations.append(invitation)
        self.save_invitations()
        return invitation

    def get_invitation(self, key: str) -> dict | None:
        """Given the 'key' part of an invitation, return the invitation.

        If the whole invitation code is passed, returns the invitation,
        possibly with updated properties (if the user passed an older version
        of the invitation).
        """
        self.check_alive()  # ensure this Blockchain object isn't shutting down

        try:
            key = json.loads(key)["key"]
        except:
            pass
        for invitation in self.invitations:
            if json.loads(invitation)["key"] == key:
                return invitation
        return None

    def delete_invitation(self, key: str) -> bool:
        """Delete an invitation."""
        self.check_alive()  # ensure this Blockchain object isn't shutting down

        invitation = self.get_invitation(key)
        if not invitation:
            return False
        self.invitations.remove(invitation)
        self.save_invitations()
        return True

    def on_join_request_received(
        self, conversation_name: str, peer_id: str
    ) -> None:
        """Process a join request from a new node."""
        self.check_alive()  # ensure this Blockchain object isn't shutting down

        logger.info(
            f"{self.name}:  on_join_request_received: received join Request"
        )
        self.peer_monitor.register_contact_event(peer_id)
        try:
            import time
            time.sleep(0.5)  # TODO: FIX THIS DELAY WITH TRNAMISSION RETRIES

            # conv.join(conversation_name, peer_id, conversation_name)
            conv = ipfs.join_conversation(
                conversation_name, peer_id, conversation_name, )
            logger.debug("WJR: joined conversation")
            invitation = conv.listen(timeout=2 * JOIN_COMMS_TIMEOUT_S).decode()
            if self.get_invitation(invitation):
                success = conv.say(
                    "All right.".encode(), timeout_sec=2 * JOIN_COMMS_TIMEOUT_S
                )
                if not success:
                    logger.debug("WJR: failed to respond to requester.")
                    conv.terminate()
                    return
                logger.debug("replied")
                appdata_zip = self.zip_appdata()

                def check_on_progress(progress: float) -> None:
                    logger.info(
                        "Sending appdata file: " + str(round(progress * 100))
                    )
                    if progress == 1:
                        os.remove(appdata_zip)
                logger.debug("WJR: Transmitting appdata...")
                sleep(0.5)
                conv.transmit_file(
                    appdata_zip,
                    "Here you go".encode(),
                    progress_handler=check_on_progress,
                    transm_send_timeout_sec=2 * JOIN_COMMS_TIMEOUT_S
                )
                logger.debug("WJR: Transmitted appdata!")
                if json.loads(invitation)["one_time"]:
                    self.delete_invitation(invitation)

            else:
                logger.info(
                    f"{self.name}:  on_join_request_received: Couldn't find "
                    f"Invitation {invitation}"
                )
                conv.say("Don't recognise Invitation.".encode())
            conv.terminate()
        except Exception as e:
            logger.error(
                f"on_join_request_received: Unhandled error {type(e)}: " + str(e))
            try:
                conv.terminate()
            except:
                pass

    def terminate(self) -> None:
        """Stop running this blockchain."""
        if self._terminate:
            return
        self._terminate = True
        self.terminate_networking()
        self.conv_lis.terminate()
        logger.info(f"{self.name}: Shut down.")

    def check_alive(self) -> None:
        """Raise an exception if this blockchain is not running."""
        if self._terminate:
            error_message = (
                f"{function_name(1)}This Walytis_Beta Blockchain has been "
                f"terminated!\n{traceback.format_stack(limit=8)}"
            )
            logger.error(error_message)
            raise BlockchainTerminatedError(error_message)


blockchains: list[Blockchain] = []


def get_blockchain_names() -> list[str]:
    """Get a list of our blockchains' names."""
    return [blockchain.name for blockchain in blockchains]


def get_blockchain_ids() -> list[str]:
    """Get a list of our blockchains' IDs."""
    return [blockchain.blockchain_id for blockchain in blockchains]


def join_blockchain(
    invitation: dict | str, blockchain_name: str = ""
) -> Blockchain | None:
    """Join a blockchain using a invitation generated by a blockchain member.

    Args:
        invitation (str): the invitation generated by a blockchain member
        blockchain_name (str): the user-chosen name for the blockchain

    Returns:
        Blockchain: the newly joined blockchain object
    """
    if isinstance(invitation, str):
        invitation_d = json.loads(invitation)
    else:
        invitation_d = invitation

    blockchain_id = invitation_d["blockchain_id"]

    if blockchain_id in get_blockchain_ids():
        logger.warning(
            "Walytis_Beta.join_blockchain: Blockchain already exists")
        return get_blockchain(blockchain_id)
    peers = invitation_d["peers"]
    logger.info("Joining blockchain...")
    for peer in peers:
        if peer == ipfs.peer_id:
            continue
        logger.debug(f"WJ: trying peer {peer}")
        tempdir = create_temp_dir()
        conv = None
        try:
            logger.debug("WJ: starting conversation")
            conv = ipfs.start_conversation(
                f"{blockchain_id}: JoinRequest: {ipfs.peer_id}",
                peer,
                f"{blockchain_id}: JoinRequest",
                dir=tempdir,
                timeout_sec=JOIN_COMMS_TIMEOUT_S
            )
            logger.info("Asking peer for AppdataZip")
            sleep(0.5)

            success = conv.say(
                json.dumps(invitation_d).encode(),
                timeout_sec=JOIN_COMMS_TIMEOUT_S
            )
            if not success:
                logger.debug("WJ: Failed to communicate with peer.")
                conv.terminate()
                continue
            response = conv.listen(JOIN_COMMS_TIMEOUT_S)
            if not response:
                logger.info("Join: No response from peer")
                conv.terminate()
                continue
            if response == "All right.".encode():
                logger.info("Join: Awaiting appdata file....")
                response = conv.listen_for_file(no_coms_timeout=180)
                if not response:
                    logger.info("Join: No file response from peer")
                    conv.terminate()
                    continue
                appdata_zipfile = os.path.join(tempdir, response["filepath"])
                logger.info(
                    f"Join: Received join Appdata! "
                    f"{appdata_zipfile}"
                )
                blockchain = join_blockchain_from_zip(
                    blockchain_id, appdata_zipfile, blockchain_name
                )
                if blockchain:  # if joining was successful
                    logger.info("Join: Joined blockchain!")
                    os.remove(appdata_zipfile)
                    conv.terminate()
                    shutil.rmtree(tempdir)
                    for _peer in peers:
                        blockchain.peer_monitor.register_contact_event(_peer)
                        pass
                    return blockchain
                else:
                    if os.path.exists(appdata_zipfile):
                        os.remove(appdata_zipfile)
                    logger.info(
                        "Join: Joining from zip file failed"
                    )
                    conv.terminate()
            else:
                logger.info(
                    "Join: Peer refused join request, peer said:"
                    f"\n{response.decode()}"
                )
                conv.terminate()
            conv.terminate()
        except Exception as e:
            logger.error(f"Join: Unhandled error {type(e)}: " + str(e))
            try:
                if conv:
                    conv.terminate()
            except Exception:
                pass

            shutil.rmtree(tempdir)
        if os.path.exists(tempdir):
            shutil.rmtree(tempdir)

    return None


def join_blockchain_from_cid(
    blockchain_id: str, blockchain_data_cid: str, blockchain_name: str = ""
) -> Blockchain | None:
    """Join an existing live blockchain from its data published on IPFS.

    Args:
        blockchain_id (str): the id of the blockchain
        blockchain_data_cid (str): path of the zip file containing the
                                    blockchain's data
        blockchain_name (str): the user-chosen name for the blockchain

    Returns:
        Blockchain: the blockchain object representing the joined blockchain
    """
    logger.info(f"Joining blockchain from CID: {blockchain_data_cid}")
    bc_appdata_path = os.path.join(get_walytis_appdata_dir(), blockchain_id)
    if [
        bc
        for bc in blockchains
        if bc.name in (blockchain_name, blockchain_id)
        or bc.blockchain_id in (blockchain_name, blockchain_id)
    ]:
        logger.info(
            "blockchain_manager.join_blockchain_from_cid:"
            "blockchain already exists"
        )
        return None
    if os.path.exists(bc_appdata_path):
        logger.info(
            "blockchain_manager.join_blockchain_from_cid:"
            + "blockchain's appdata path already exists"
        )
        return None
    logger.debug("WJ: getting join data from IPFS...")
    ipfs.files.download(blockchain_data_cid, dest_path=bc_appdata_path)
    logger.debug("WJ: got join data from IPFS!")

    return check_and_start_joined_blockchain(blockchain_id, blockchain_name)


def join_blockchain_from_zip(
    blockchain_id: str, blockchain_zip_path: str, blockchain_name: str = ""
) -> Blockchain | None:
    """Join an existing live blockchain from zip file containing its data.

    Paramaters:
        blockchain_id(str): the id of the blockchain
        blockchain_zip_path: path of the zip file containing the blockchain's
                                data
        blockchain_name(str): the chosen name for the blockchain
    Returns:
        Blockchain: the blockchain object representing the joined blockchain
    """
    bc_appdata_path = os.path.join(get_walytis_appdata_dir(), blockchain_id)
    if [
        bc
        for bc in blockchains
        if bc.name in (blockchain_name, blockchain_id)
        or bc.blockchain_id in (blockchain_name, blockchain_id)
    ]:
        logger.info(
            "blockchain_manager.join_blockchain_from_zip:"
            "blockchain already exists"
        )
        return None
    if os.path.exists(bc_appdata_path):
        logger.info(
            "blockchain_manager.join_blockchain_from_zip:"
            + "blockchain's appdata path already exists"
        )
        return None

    shutil.unpack_archive(
        os.path.abspath(blockchain_zip_path), bc_appdata_path, "zip"
    )
    return check_and_start_joined_blockchain(blockchain_id, blockchain_name)


def check_and_start_joined_blockchain(
    blockchain_id: str, blockchain_name: str
) -> Blockchain | None:
    """Check a blockchain's validity and run it.

    Called after a newly joined blockchain's appdata has been installed.
    """
    try:
        blockchain: Blockchain = Blockchain(
            blockchain_id, name=blockchain_name
        )
        logger.debug("WJ: Reconstructed blockchain.")

        blockchains.append(blockchain)

        genesis_block = blockchain.load_block(
            blockchain.load_latest_block_ids()[0]
        )
        if not genesis_block:
            logger.warning(
                "Joining blockchain cancelled because it seems "
                "corrupt: we couldn't find its genesis block. "
                f"{blockchain_id}"
            )
            delete_blockchain(blockchain_id)
            return None
        blockchain_ok = True
        if not (
            genesis_block.ipfs_cid == blockchain_id
            or blockchain_id in ["BrenthyUpdates", "BrenthyUpdatesTEST"]
        ):
            logger.warning(
                "Joining blockchain cancelled because the "
                "blockchain ID did not match the genesis block. "
                f"{blockchain_id}"
            )
            blockchain_ok = False

        if not len(genesis_block.parents) == 0:
            logger.warning(
                "Joining blockchain canceled because the "
                f"genesis block has parents. {len(genesis_block.parents)}"
            )
            blockchain_ok = False
        if not blockchain_ok:
            delete_blockchain(blockchain_id)
            return None
        logger.debug("WJ: checked joined blockchain")
        return blockchain
    except Exception as error:
        logger.error(error)
        return None


def create_blockchain(blockchain_name: str = "") -> Blockchain | None:
    """Create a new blockchain.

    Args:
        blockchain_name (str): the id of the blockchain to create (unique)

    Returns:
        Blockchain: the newly created Blockchain object
    """
    if (
        blockchain_name
        and [bc for bc in blockchains if bc.name == blockchain_name]
        or [bc for bc in blockchains if bc.blockchain_id == blockchain_name]
    ):
        logger.info(
            "blockchain_manager.create_blockchain: blockchain already exists"
        )
        return None
    # create new blockchain
    blockchain = Blockchain(None, name=blockchain_name)
    blockchains.append(blockchain)
    # app_data.SaveBlockchainsList([bc.name for bc in blockchains])

    return blockchain


def delete_blockchain(blockchain_id: str) -> bool:
    """Delete a blockchain.

    Args:
        blockchain_id (bytearray): the id of the blockchain to delete

    Returns:
        bool success: whether or not the specified blockchain was found.
    """
    logger.debug("trying to delete blockchain")
    blockchain_search = [
        bc for bc in blockchains if bc.blockchain_id == blockchain_id
    ]
    if blockchain_search:
        blockchain: Blockchain = blockchain_search[0]
        logger.important(
            f"deleting blockchain {blockchain.name}..."
        )
        if blockchain in blockchains:
            blockchains.remove(blockchain)
        else:
            logger.warning(
                "walytis_beta.delete_blockchain: "
                "blockchain not in blockchains list"
            )
        blockchain.terminate()
        blockchain._blocks_finder_thread.join()
        blockchain.block_requester_thread.join()
        blockchain.index_lock.acquire()
        if os.path.exists(blockchain.appdata_dir):
            shutil.rmtree(blockchain.appdata_dir)
        else:
            logger.warning(
                "delete_blockchain: blockchain's appdata path "
                f"doesn't exist {blockchain.appdata_dir}"
            )
        blockchain.index_lock.release()
        logger.important(f"deleted blockchain {blockchain.name}")
        logger.info(
            "Walytis_Beta:remaining blockchains: "
            f"{[blockchain.name for blockchain in blockchains]}"
        )

        return True

    logger.warning(
        f"delete_blockchain: no such blockchain {blockchain_id}"
    )
    return False


def get_blockchains() -> list[Blockchain]:
    """Get a list of the currently running blockchains."""
    return blockchains


def get_blockchain(blockchain_id: str) -> Blockchain | None:
    """Get a blockchain object given its ID."""
    for blockchain in blockchains:
        if blockchain.blockchain_id == blockchain_id:
            return blockchain
    return None


require_blockchain_paths = {"KnownBlocksIndex", "ReceivedBlocks"}


def run_blockchains() -> None:
    """Start running our blockchains."""
    if not get_walytis_appdata_dir():
        error_message = (
            "Walytis appdata directory not set!\n"
            "Call `walytis_api.set_appdata_dir() before calling run_blockchains`"
        )
        logger.error(error_message)
        raise Exception(error_message)
    blockchain_ids = []
    logger.important(
        "Loading blockchains from "
        f"{os.path.abspath(get_walytis_appdata_dir())}"
    )
    for blockchain_id in os.listdir(get_walytis_appdata_dir()):
        blockchain_data_dir = os.path.join(
            get_walytis_appdata_dir(), blockchain_id
        )

        if os.path.isdir(blockchain_data_dir):
            if not require_blockchain_paths.issubset(
                set(os.listdir(blockchain_data_dir))
            ):
                logger.important(f"Skipping directory {blockchain_data_dir}")
                continue
            blockchain_ids.append(blockchain_id)
        else:  # delete uncleanedup file
            os.remove(blockchain_data_dir)

    logger.important("Running blockchains:")
    for blockchain_id in blockchain_ids:
        if get_blockchain(blockchain_id):
            logger.important(
                f"run_blockchains: already loaded: {blockchain_id}")
            continue
        blockchain = Blockchain(id=blockchain_id, name="")
        logger.important(f" - {blockchain.name}")
        blockchains.append(blockchain)


def terminate() -> None:
    """Stop all running blockchains."""
    logger.debug("Terminating all blockchains...")
    global blockchains
    threads: list[Thread] = []
    for blockchain in blockchains:
        thread = Thread(target=blockchain.terminate, args=())
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    blockchains = []
    logger.debug("Terminated all blockchains!")
    ipfs.terminate()
    logger.debug("Terminated IPFS!")
