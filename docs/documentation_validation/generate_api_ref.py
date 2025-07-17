"""Generate an HTML website for the API reference of `walytis_beta_api`."""

import os
import shutil

PROJECT_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", ".."
))
SRC_DIR = os.path.join(
    PROJECT_DIR, "src"
)
TEMPLATES_DIR = os.path.abspath(os.path.join(
    PROJECT_DIR, "..",  "..",  "..",  "..", "..", "pdoc-templates"
))
docs_path = os.path.join("docs", "API-Reference")
if os.path.exists(docs_path):
    shutil.rmtree(docs_path)

modules = {
    "walytis_beta_api": [
        "blockchain_model",
        "block_model",
        "exceptions",
        "walytis_beta_interface",
    ],
    "walytis_beta_tools": [
        "block_model",
        "exceptions"
    ]
}
for module_name in modules.keys():
    module_path = os.path.join(SRC_DIR, module_name)
    command = (
        f"pdoc3 {module_path} "
        f"--html --force -o {docs_path} --template-dir {TEMPLATES_DIR}"
    )
    submodule_filters = modules[module_name]
    if submodule_filters:

        command += f" --filter {','.join(submodule_filters)}"

    print(command)
    os.system(command)
