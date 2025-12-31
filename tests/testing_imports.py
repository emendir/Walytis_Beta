"""Script to import project source for tests."""

from emtest import assert_is_loaded_from_source
from emtest import (
    add_path_to_python,
    are_we_in_docker,
)
import os


from testing_paths import WORKDIR, SRC_DIR, EMBEDDED_DIR


def load_walytis():
    # ensure IPFS is initialised via Walytis_Beta.networking, not walytis_beta_api
    from walytis_beta_tools._experimental.config import (
        WalytisTestModes,
        get_walytis_test_mode,
    )

    if get_walytis_test_mode() == WalytisTestModes.EMBEDDED:
        os.environ["WALYTIS_BETA_API_TYPE"] = "WALYTIS_BETA_DIRECT_API"
    import walytis_beta_api
    import walytis_beta_embedded
    import walytis_beta_tools

    if not are_we_in_docker():
        assert_is_loaded_from_source(EMBEDDED_DIR, walytis_beta_embedded)
        assert_is_loaded_from_source(SRC_DIR, walytis_beta_api)
        assert_is_loaded_from_source(SRC_DIR, walytis_beta_tools)
    walytis_appdata_path = os.path.abspath(".blockchains")
    walytis_beta_embedded.set_appdata_dir(walytis_appdata_path)
    print(f"Walytis Appdata: {walytis_appdata_path}")
