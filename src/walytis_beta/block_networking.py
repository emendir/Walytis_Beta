"""The networking machinery of the Block class."""

# from random import seed
# from random import randint
import json
import os
from tempfile import NamedTemporaryFile

from threading import Thread
from walytis_beta_tools.log import logger_networking as logger
from brenthy_tools_beta.utils import (  # pylint: disable=unused-import
    bytes_to_string,
)

from walytis_beta_tools import block_model

from .networking import ipfs

PREFERRED_HASH_ALGORITHM = "sha512"


class Block(block_model.Block):
    """The Walytis_Beta block.

    The networking functionality is defined in this child class,
    its parent block_model.Block contains the more fundamental functionality.
    """

    def publish_and_generate_id(
        self, blockchain_id: str, skip_pubsub: bool = False
    ) -> None:
        """Publish this block, generating its long ID."""
        # make sure all the necessary components of the short_id have been set
        if not (len(self.creator_id) != 0 and len(self._content_hash) != 0):
            return

        if not (len(self.file_data) > 0):
            error_message = "Block.publish_file_data: file_data is empty"
            logger.error(error_message)
            raise ValueError(error_message)

        logger.info("Publishing file...")
        tempf = NamedTemporaryFile(delete=False)
        tempf.write(self.file_data)
        tempf.close()
        cid = ipfs.files.predict_cid(tempf.name)
        if cid in ipfs.files.list_pins(cache_age_s=1000):
            logger.error(
                "Block.publish_file_data: "
                "IPFS content with this CID already exists!"
            )
            raise IpfsCidExistsError()
        self._ipfs_cid = cid

        logger.debug("Block: generating ID...")
        self.generate_id()

        def _publish(short_id: str) -> None:
            logger.debug("Publishing...")
            cid = ipfs.files.publish(tempf.name)
            os.remove(tempf.name)
            logger.debug("Pinning...")
            ipfs.files.pin(cid)
            if not skip_pubsub:
                # Publish a PubSub message about the new block.
                logger.debug("Block: announcing on pubsub")
                if not short_id:
                    raise Exception("Announce block on PubSub: empty block ID")
                data = json.dumps(
                    {
                        "message": "New block!",
                        "block_id": bytes_to_string(short_id),
                    }
                ).encode()

                ipfs.pubsub.publish(blockchain_id, data)
            logger.debug("Published!")

        Thread(
            target=_publish,
            args=(self.short_id,),
            name="Block-Publisher-Temp",
        ).start()


class IpfsCidExistsError(Exception):
    """When publishing a new block but the intended IPFS CID already exists."""

    message = "An IPFS file with this content ID already exists!"

    def __str__(self):
        """Get this exception's error message."""
        return self.message
