import os
from ipfs_tk_generics.client import IpfsClient
from walytis_beta_tools.log import logger

from enum import Enum
from environs import Env

env = Env()
# initialise IPFS
USE_IPFS_NODE = os.environ.get("USE_IPFS_NODE", "").lower() in ["true", "1"]
DEF_IPFS_REPO_DIR = os.path.abspath(os.path.join(".ipfs_repo"))
IPFS_REPO_DIR = env.str("IPFS_REPO_DIR", DEF_IPFS_REPO_DIR)
ipfs: IpfsClient


class IpfsTkModes(Enum):
    EMBEDDED = "EMBEDDED"
    HTTP = "HTTP"


def get_ipfs_tk_mode() -> IpfsTkModes:
    return env.enum(
        "IPFS_TK_MODE",
        enum=IpfsTkModes,
        default=IpfsTkModes.HTTP,
    )


class WalytisTestModes(Enum):
    EMBEDDED = "EMBEDDED"
    USE_BRENTHY = "USE_BRENTHY"
    RUN_BRENTHY = "RUN_BRENTHY"


def get_walytis_test_mode() -> WalytisTestModes:
    return env.enum(
        "WALYTIS_TEST_MODE",
        enum=WalytisTestModes,
        default=WalytisTestModes.EMBEDDED,
    )


class WalytisBetaApiTypes(Enum):
    WALYTIS_BETA_BRENTHY_API = 0
    WALYTIS_BETA_DIRECT_API = 1


def get_walytis_beta_api_type():
    return env.enum(
        "WALYTIS_BETA_API_TYPE",
        enum=WalytisBetaApiTypes,
        default=WalytisBetaApiTypes.WALYTIS_BETA_BRENTHY_API,
    )
