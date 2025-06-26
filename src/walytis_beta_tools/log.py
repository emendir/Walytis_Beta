import logging
import os
from logging.handlers import RotatingFileHandler

# Formatter
# formatter = logging.Formatter(
#     '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
# )
MAX_RECORD_NAME_LENGTH=16

class AlignedFormatter(logging.Formatter):
    def format(self, record):
        # Save original levelname for internal use
        original_levelname = record.levelname
        if len(record.name) > MAX_RECORD_NAME_LENGTH:
            record.name = record.name[:MAX_RECORD_NAME_LENGTH]
        # Format: [LEVEL] + padding (outside brackets)
        padded_level = f"[{original_levelname}]" + " " * (10 - len(original_levelname))
        record.padded_level = padded_level

        return super().format(record)
formatter = AlignedFormatter(
    f'%(asctime)s %(padded_level)s %(name)-{MAX_RECORD_NAME_LENGTH}s: %(message)s'
)
# Console handler (INFO+)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

LOG_PATH = os.path.abspath(os.environ.get("WALYTIS_BETA_LOG_PATH", "Walytis_Beta.log"))
# print(f"Walytis_Beta: Logging to {LOG_PATH}")
# File handler (DEBUG+ with rotation)
file_handler = RotatingFileHandler(
    'Walytis_Beta.log', maxBytes=5*1024*1024, backupCount=5
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)


# Log level IMPORTANT
IMPORTANT_LEVEL_NUM = 25
logging.addLevelName(IMPORTANT_LEVEL_NUM, "IMPORTANT")
def important(self, message, *args, **kwargs):
    if self.isEnabledFor(IMPORTANT_LEVEL_NUM):
        self._log(IMPORTANT_LEVEL_NUM, message, args, **kwargs)

logging.Logger.important = important


# # Root logger
# logger_root = logging.getLogger()
# logger_root.setLevel(logging.DEBUG)  # Global default
# logger_root.addHandler(console_handler)
# # logger_root.addHandler(file_handler)

logger = logging.getLogger("Walytis")
logger.setLevel(logging.DEBUG)


logger_networking = logging.getLogger("Walytis.Networking")
logger_api = logging.getLogger("Walytis.API")
logger_block_creation = logging.getLogger("Walytis.BlockCreation")
logger_block_processing = logging.getLogger("Walytis.BlockProcess")
logger_block_records = logging.getLogger("Walytis.BlockRecords")
logger_blockchain_model = logging.getLogger("Walytis.BlockchModel")
logger_block_model = logging.getLogger("Walytis.BlockModel")
logger_generics = logging.getLogger("Walytis.Generics")
logger_ancestry = logging.getLogger("Walytis.Ancestry")
logger_appdata = logging.getLogger("Walytis.Appdata")

logger.setLevel(IMPORTANT_LEVEL_NUM)
logger_networking.setLevel(IMPORTANT_LEVEL_NUM)
logger_api.setLevel(IMPORTANT_LEVEL_NUM)
logger_block_creation.setLevel(IMPORTANT_LEVEL_NUM)
logger_block_processing.setLevel(IMPORTANT_LEVEL_NUM)
logger_block_records.setLevel(IMPORTANT_LEVEL_NUM)
logger_blockchain_model.setLevel(IMPORTANT_LEVEL_NUM)
logger_block_model.setLevel(IMPORTANT_LEVEL_NUM)
logger_generics.setLevel(IMPORTANT_LEVEL_NUM)
logger_ancestry.setLevel(IMPORTANT_LEVEL_NUM)
logger_appdata.setLevel(IMPORTANT_LEVEL_NUM)

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
