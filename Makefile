# =========================================================
# Generic Python Project Makefile
# =========================================================
# Usage:
#   make <target>
#
# Run `make help` to see available targets.
# =========================================================

# Variables
PYTHON      ?= python3
PIP         ?= $(PYTHON) -m pip
DIST_DIR    := dist

# Default target
.PHONY: all
all: check build ## Run checks and build the package

# ----------------------------
# Dependency Management
# ----------------------------
.PHONY: deps
deps: ## Install dependencies from requirements.txt
	$(PIP) install -r requirements.txt

# ----------------------------
# Quality & Testing
# ----------------------------
.PHONY: test lint typecheck format check coverage

test: ## Run test suite with pytest
	$(PYTHON) -m pytest -v tests

# lint: ## Lint code with ruff
# 	ruff check src tests
#
# typecheck: ## Type-check with mypy
# 	mypy src tests

format: ## Autoformat code with ruff
	ruff format src tests

# check: lint typecheck test ## Run lint, typecheck, and test

coverage: ## Run tests with coverage report
	$(PYTHON) -m pytest --cov=src --cov-report=term-missing

# ----------------------------
# Build & Packaging
# ----------------------------
.PHONY: build clean install

build: clean ## Build distribution package
	$(PYTHON) -m build

clean: ## Remove items from CLEANUP section in .gitignore
	@tmpfile=$$(mktemp); \
	sed -n '/# >>> CLEANUP/,/# <<< CLEANUP/p' .gitignore \
		| grep -v '^#' \
		| grep -v '^[[:space:]]*$$' > $$tmpfile; \
	git ls-files --ignored --exclude-from=$$tmpfile --others --directory -z \
		| xargs -0 rm -rf; \
	rm $$tmpfile; \
	$(MAKE) -C docs/_docs_tools clean

# install: build ## Install built wheel into environment
# 	$(PIP) install $(DIST_DIR)/*.whl

# ----------------------------
# Documentation
# ----------------------------
.PHONY: docs

docs: ## Build Sphinx documentation
	$(MAKE) -C docs/_docs_tools all

.PHONY: hanuki

hanuki: ## Open project in web-browser
	@cid=$$(ipfs add -rHq . | tail -n 1 | xargs ipfs cid base32); \
			brave-browser "http://$$cid.ipfs.localhost:8080"
# # ----------------------------
# # Release Helpers
# # ----------------------------
# .PHONY: dist upload
#
# dist: build ## List built distributions
# 	ls -lh $(DIST_DIR)
#
# upload: build ## Upload package to PyPI (requires twine)
# 	twine upload $(DIST_DIR)/*

# ----------------------------
# Help
# ----------------------------
.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'


