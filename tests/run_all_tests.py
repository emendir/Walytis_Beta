"""Run all tests in all variations."""

from datetime import datetime
import os
import sys

from emtest import set_env_var

WORKDIR = os.path.dirname(__file__)

pytest_args = sys.argv[1:]


TEST_FUNC_TIMEOUT_SEC = 300


def run_tests() -> None:
    """Run each test file with pytest."""
    pytest_args = sys.argv[1:]
    timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    os.system(
        f"{sys.executable} -m pytest {WORKDIR} "
        f"--html=report-{timestamp}/report.html "
        f"--json=report-{timestamp}/report.json "
        f"--timeout={TEST_FUNC_TIMEOUT_SEC} "
        f"{' '.join(pytest_args)}"
    )


if True:
    os.chdir(WORKDIR)
    import conftest  # noqa
    from build_docker import build_docker_image
build_docker_image(verbose=False)

set_env_var("TESTS_REBUILD_DOCKER", False)

set_env_var("WALYTIS_TEST_MODE", "RUN_BRENTHY")
print("Running tests with Brenthy...")
run_tests()

set_env_var("WALYTIS_TEST_MODE", "EMBEDDED")
print("Running tests with Walytis Embedded...")
run_tests()

os.system(
    "docker ps - -filter 'reference=brenthy_testing' - aq | docker rm - f"
)
