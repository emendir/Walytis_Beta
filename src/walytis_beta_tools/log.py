from emtest.log_utils import get_app_log_dir
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Formatter
# formatter = logging.Formatter(
#     '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
# )
MAX_RECORD_NAME_LENGTH = 16


class MillisecondFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created)

        result = dt.strftime(datefmt)

        # convert microseconds to milliseconds
        if datefmt[-2:] == "%f":
            result = result[:-3]

        return result


LOG_TIMESTAMP_FORMAT = "%Y-%m-%d~%H:%M:%S.%f"

# Formatter
formatter = MillisecondFormatter(
    "%(asctime)s [%(levelname)-8s] %(name)-16s | %(message)s",
    datefmt=LOG_TIMESTAMP_FORMAT,
)
# Console handler (INFO+)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)


logger = logging.getLogger("Walytis")
logger_networking = logging.getLogger("Networking")
logger_api = logging.getLogger("API")
logger_block_creation = logging.getLogger("BlockCreation")
logger_block_processing = logging.getLogger("BlockProcess")
logger_block_records = logging.getLogger("BlockRecords")
logger_blockchain_model = logging.getLogger("BlockchainModel")
logger_block_model = logging.getLogger("BlockModel")
logger_generics = logging.getLogger("Generics")
logger_ancestry = logging.getLogger("Ancestry")
logger_appdata = logging.getLogger("Appdata")
logger_join = logging.getLogger("Join")

logger.setLevel(logging.DEBUG)
logger_networking.setLevel(logging.DEBUG)
logger_api.setLevel(logging.DEBUG)
logger_block_creation.setLevel(logging.DEBUG)
logger_block_processing.setLevel(logging.DEBUG)
logger_block_records.setLevel(logging.DEBUG)
logger_blockchain_model.setLevel(logging.DEBUG)
logger_block_model.setLevel(logging.DEBUG)
logger_generics.setLevel(logging.DEBUG)
logger_ancestry.setLevel(logging.DEBUG)
logger_appdata.setLevel(logging.DEBUG)
logger_join.setLevel(logging.DEBUG)

logger.addHandler(console_handler)
logger_networking.addHandler(console_handler)
logger_api.addHandler(console_handler)
logger_block_creation.addHandler(console_handler)
logger_block_processing.addHandler(console_handler)
logger_block_records.addHandler(console_handler)
logger_blockchain_model.addHandler(console_handler)
logger_block_model.addHandler(console_handler)
logger_generics.addHandler(console_handler)
logger_ancestry.addHandler(console_handler)
logger_appdata.addHandler(console_handler)
logger_join.addHandler(console_handler)


file_handler = None
WALYTIS_BETA_TOOLS_LOG_NAME = os.environ.get(
    "WALYTIS_BETA_TOOLS_LOG_NAME", "Walytis_Beta"
)
LOG_DIR = get_app_log_dir(WALYTIS_BETA_TOOLS_LOG_NAME, "Waly")
if LOG_DIR is None:
    logger.info("Logging to files is disabled.")
else:
    LOG_PATH = os.path.join(LOG_DIR, f"{WALYTIS_BETA_TOOLS_LOG_NAME}.log")
    logger.info(f"Logging to {os.path.abspath(LOG_PATH)}")

    file_handler = RotatingFileHandler(
        LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger_networking.addHandler(file_handler)
    logger_api.addHandler(file_handler)
    logger_block_creation.addHandler(file_handler)
    logger_block_processing.addHandler(file_handler)
    logger_block_records.addHandler(file_handler)
    logger_blockchain_model.addHandler(file_handler)
    logger_block_model.addHandler(file_handler)
    logger_generics.addHandler(file_handler)
    logger_ancestry.addHandler(file_handler)
    logger_appdata.addHandler(file_handler)
    logger_join.addHandler(file_handler)
