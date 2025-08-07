![](./graphics/WalytisIcon.png)




# [Walytis](https://github.com/emendir/WalytisTechnologies/blob/master/Walytis/Meaning/IntroductionToWalytis.md)

**_A flexible, lightweight, nonlinear blockchain, serving as a p2p distributed database._**
_`4D61646520776974682073696E63657265206C6F766520666F72206D616E6B696E642E`_

Walytis is a database-blockchain, a type of blockchain that is nothing more than a fully distributed database-management system, with a focus on accessibility, flexibility and lightweightedness, when compared to other blockchains.
Applications can create a new Walytis database-blockchain whenever they need one.
While they can always add new data to it, existing data can never be deleted or modified.

## Applications: Examples of Use Cases

- [Messenger](https://github.com/emendir/Endra): A database-blockchain can be used to record the existence of messages in a chatroom. Actual message content is stored off-chain for privacy. In this case the database-blockchain is used not for storage but to help the various devices of the member's chatroom coordinate their data synchronisation.
  
- File Synchronisation: File changes are recorded in blocks, creating a complete unified history of file edits across users. Actual files are stored off-chain for storage-efficiency.
  
- Serverless Git Collaboration: Ever notice that git already looks like a blockchain? Map git commits onto Walytis blocks and git repositories onto Walytis blockchains and you've got a shared git repo!
  
- [Identity Management](https://github.com/emendir/WalytisIdentities): One data-base blockchain is used for every identity, publishing [DID-documents](https://www.w3.org/TR/did-1.0/) as blocks, cryptographically authenticated
  
To learn about projects built on Walytis under active development, see https://github.com/emendir/WalytisTechnologies

### Blockchain Overlays

The features of Walytis blockchains can be expanded by building modules on top of them that provide applications with interfaces to database-blockchains that have unique features and functionality not built into Walytis.
Currently under development are tools for off-chain and encrypted data storage, authentication, access-control, identity-management and mutable data structures are built in a modular way so that application developers can choose which extra features they need for their use case. These modules can be compounded to combine their features.


Learn about Walytis here: [Introduction to Walytis](https://github.com/emendir/WalytisTechnologies/blob/master/Walytis/Meaning/IntroductionToWalytis.md)
Learn why Walytis was developed: [Walytis' Rationale](https://github.com/emendir/WalytisTechnologies/blob/master/Walytis/Meaning/WalytisRationale.md)


## Getting Started

### 1. Install or Run from Source

Install Walytis to run on your system as a background service using [Brenthy](https://github.com/emendir/BrenthyAndWalytis/):

Ubuntu quick start:

```sh
# install prerequisites
sudo apt update && sudo apt install -y python3-virtualenv git

# download BrenthyAndWalytis
git clone https://github.com/emendir/BrenthyAndWalytis
cd BrenthyAndWalytis

# install the Walytis blockchain
Brenthy/blockchains/install_walytis_beta.sh

# set up python environment (you can skip this if you only want to install)
virtualenv .venv && source .venv/bin/activate
pip install -r Brenthy/requirements.txt
pip install walytis_beta_api    # install API library

# run Brenthy, it will offer to install itself
python3 .
```

Brenthy wil ask you whether you want to install or run it from source.

For details on how to run Brenthy & Walytis, see [Running From Source](https://github.com/emendir/BrenthyAndWalytis/blob/master/Documentation/Brenthy/User/RunningFromSource.md)

For details on how to install Brenthy & Walytis, see [Installing Brenthy](https://github.com/emendir/BrenthyAndWalytis/blob/master/Documentation/Brenthy/User/InstallingBrenthy.md)

### 2. Use Walytis

1. Install the `walytis_beta_api` Python package:

```sh
pip install walytis_beta_api
```

2. Start playing around in Python:

```python
import walytis_beta_api as waly

# create a database
blockchain = waly.Blockchain.create("MyFirstBlockchain")

# add data to the database
block = blockchain.add_block(content="Hello there!".encode(), topics=["testing"])

invitation = blockchain.create_invitation()
print(invitation)
```

On another computer, join the newly created blockchain:
```python
invitation = # paste invitation from above

import walytis_beta_api as waly

# join the database created on the first computer
blockchain = waly.Blockchain.join(invitation)

# read newest block from the database
block = blockchain.get_block(-1)
print(block.content)
print(block.creation_time)
print(block.topics)
```

Read the [Tutorial](https://github.com/emendir/WalytisTechnologies/blob/master/Walytis/Tutorials/0-TutorialOverview.md) to learn how to use Walytis, and start building cool stuff!

## Documentation

To learn how Walytis works, read its documentation, which lives in a dedicated repository:
- https://github.com/emendir/WalytisTechnologies/blob/master/Walytis/DocsOverview.md

For notes on how to use the python API, see the [walytis_beta_api library's API reference](./docs/API-Reference/walytis_beta_api/index.html).

## Contributing

### Analysis and Review

If you have any thoughts on Walytis or want to discuss the sensibility of their unique features, feel free to share them under GitHub discussions.
I would especially appreciate reviews and analyses of [Walytis' blockchain-architecture security](https://github.com/emendir/WalytisTechnologies/blob/master/Walytis/Technical/WalytisBlockchainSecurity.md).

### Software Development

Despite the documentation on Brenthy & Walytis' DevOps not being written yet, feel free to submit pull requests via GitHub if you think you know what you're doing.

### Feature Requests and Bug Reports

If you don't have the time to learn how to contribute code directly, feel free to request features or report bugs via GitHub Issues.

### Financial Support

To financially support me in my work on this and other projects, you can make donations with the following currencies:

- **Bitcoin:** `BC1Q45QEE6YTNGRC5TSZ42ZL3MWV8798ZEF70H2DG0`
- **Ethereum:** `0xA32C3bBC2106C986317f202B3aa8eBc3063323D4`
- [**Fiat** (via Credit or Debit Card, Apple Pay, Google Pay, Revolut Pay)](https://checkout.revolut.com/pay/4e4d24de-26cf-4e7d-9e84-ede89ec67f32)


### About the Developer

Walytis and the derived technologies listed here are developed by me, a human, publishing my open-source works under the name of _Emendir_. 

## Related Projects
### The Endra Tech Stack

- [IPFS](https://ipfs.tech):  A p2p communication and content addressing protocol developed by ProtocolLabs.
- [Walytis](https://github.com/emendir/Walytis_Beta): A flexible, lightweight, nonlinear database-blockchain, built on IPFS.
- [WalytisIdentities](https://github.com/emendir/WalytisIdentities): P2P multi-controller cryptographic identity management, built on Walytis.
- [WalytisOffchain](https://github.com/emendir/WalytisOffchain): Secure access-controlled database-blockchain, built on WalytisIdentities.
- [WalytisMutability](https://github.com/emendir/WalytisMutability): A Walytis blockchain overlay featuring block mutability.
- [Endra](https://github.com/emendir/Endra): A p2p encrypted messaging protocol with multiple devices per user, built on Walytis.
- [EndraApp](https://github.com/emendir/EndraApp): A p2p encrypted messenger supporting multiple devices per user, built on Walytis.

### Alternative Technologies

- [OrbitDB](https://orbitdb.org/): a distributed IPFS-based database written in go
