## Testing

### Test Machinery Overview

Walytis' testing system is based on the pytest framework.
Some tests are simple pytest scripts.
The more advanced tests leverage docker containers to test communications between multiple Walytis nodes.

### Test Environment

Walytis' testing system needs to be run in an environment that has the following components installed:

- docker
- ipfs
- python
- python packages listed in [/requirements.txt](/requirements.txt) and [/requirements-devops.txt](/requirements-devops.txt)

For example, setting up a testing environment can be as simple as installing docker and python on your computer and running `pip install -r $FILENAME` on the the two requirements files.

### Source Code

You need the Brenthy and nested Walytis source code to run the full test suite.

```sh
# download BrenthyAndWalytis
git clone https://github.com/emendir/BrenthyAndWalytis
cd BrenthyAndWalytis

# install the Walytis blockchain
Brenthy/blockchains/install_walytis_beta.sh
```

### Running Tests

In an appropriate testing environment as described above, ensure IPFS is running, then run the tests located in the `tests` folder with pytest.

```sh
cd Brenthy/Brenthy/blockchains/Walytis_Beta/tests
```

Make sure Brenthy is NOT running separately.
Run the test file `./tests/test_walytis_beta.py` with all logging enabled (`-s`) and debugger for failed tests enabled (`--pdb`)

```sh
pytest test_walytis_beta.py -s --pdb
```

Run all tests and use pytest's default console output instead of the simpler default used by Walytis:

```sh
DEFAULT_TERMINAL_REPORTER=1 pytest ./tests
```

Run a test using an embedded Walytis node:

```sh
WALYTIS_TEST_MODE=EMBEDDED pytest ./tests/test_walytis_beta.py -s --pdb
```

Run a test using a Walytis node to be run in Brenthy:

```sh
WALYTIS_TEST_MODE=RUN_BRENTHY pytest ./tests/test_walytis_beta.py -s --pdb
```

Run a test with a Walytis node already running in Brenthy separately:

```sh
WALYTIS_TEST_MODE=USE_BRENTHY pytest ./tests/test_walytis_beta.py -s --pdb
```
