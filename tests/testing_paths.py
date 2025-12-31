from emtest import (
    add_path_to_python,
)
import os


WORKDIR = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.dirname(WORKDIR)
SRC_DIR = os.path.join(PROJ_DIR, "src")
EMBEDDED_DIR = os.path.join(
    PROJ_DIR, "legacy_packaging", "walytis_beta_embedded"
)
BRENTHY_DIR = os.path.join(PROJ_DIR, "..", "..", "..", "Brenthy")
BRENTHY_DOCKER_DIR = os.path.join(BRENTHY_DIR, "..", "tests", "brenthy_docker")


# add source code paths to python's search paths
add_path_to_python(SRC_DIR)
add_path_to_python(EMBEDDED_DIR)
add_path_to_python(BRENTHY_DIR)
add_path_to_python(BRENTHY_DOCKER_DIR)
