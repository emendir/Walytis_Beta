from .config import (
    get_ipfs_tk_mode,
    IpfsTkModes,
    IPFS_REPO_DIR,
    DEF_IPFS_REPO_DIR,
)

from walytis_beta_tools.log import logger
import os

if get_ipfs_tk_mode() == IpfsTkModes.EMBEDDED:
    if not os.path.exists(IPFS_REPO_DIR):
        if IPFS_REPO_DIR == DEF_IPFS_REPO_DIR:
            os.makedirs(IPFS_REPO_DIR)
        else:
            raise Exception(
                "The path specified in the environment variable IPFS_REPO_DIR "
                f"doesn't exist: {IPFS_REPO_DIR}"
            )

    print(f"IPFS repo: {IPFS_REPO_DIR}")
    from ipfs_node import IpfsNode

    ipfs = IpfsNode(IPFS_REPO_DIR)
else:
    from ipfs_remote import IpfsRemote

    ipfs = IpfsRemote()
    try:
        ipfs.wait_till_ipfs_is_running(timeout_sec=5)
    except TimeoutError:
        logger.warning("IPFS isn't running. Waiting for IPFS to start...")
        ipfs.wait_till_ipfs_is_running()
        logger.warning("IPFS running now.")
