#!/bin/bash

# the absolute paths of this script and it's directory
SCRIPT_DIR="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

cd "$SCRIPT_DIR"

BUILD_DIR="${SCRIPT_DIR}/_build"
DOCS_DIR=$(realpath "$SCRIPT_DIR/..")
SRC_DIR=$(realpath "$SCRIPT_DIR/../../src")
OUTPUT_DIR="${DOCS_DIR}/html"

# Path to the folder with stubs generated py sphinx-apidoc
SPHINX_CONF_DIR=${SCRIPT_DIR}/sphinx_config
API_REF_TEMPLATE=${SPHINX_CONF_DIR}/API-Reference

