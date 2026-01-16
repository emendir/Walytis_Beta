"""Run all tests in all variations."""

from datetime import datetime
import os
import sys

from emtest import set_env_var, env_vars

WORKDIR = os.path.dirname(__file__)

pytest_args = sys.argv[1:]


TEST_FUNC_TIMEOUT_SEC = 300
REPORTS_DIR_PREF = env_vars.str("TESTS_REPORTS_DIR_PREF", default="report")


def run_tests() -> None:
    """Run each test file with pytest."""
    pytest_args = sys.argv[1:]
    timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    os.system(
        f"{sys.executable} -m pytest {WORKDIR} "
        f"--html={REPORTS_DIR_PREF}-{timestamp}/report.html "
        f"--json={REPORTS_DIR_PREF}-{timestamp}/report.json "
        f"--timeout={TEST_FUNC_TIMEOUT_SEC} "
        f"{' '.join(pytest_args)}"
    )


os.system("sudo systemctl stop brenthy")
os.system("sudo systemctl start ipfs")

if True:
    os.chdir(WORKDIR)
    import conftest  # noqa
    from build_docker import build_docker_image

if env_vars.bool("TESTS_REBUILD_DOCKER", default=True):
    build_docker_image(verbose=False)

set_env_var("TESTS_REBUILD_DOCKER", False)

# Test Procedure (Post-Prep)

set_env_var("WALYTIS_TEST_MODE", "RUN_BRENTHY")
print("Running tests with Brenthy...")
run_tests()

set_env_var("WALYTIS_TEST_MODE", "EMBEDDED")
print("Running tests with Walytis Embedded...")
run_tests()

os.system(
    "docker ps --filter 'ancestor=brenthy_testing' - aq | docker rm - f || true"
)
