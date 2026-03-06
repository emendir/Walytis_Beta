![](./graphics/WalytisIcon.png)




# [Walytis](https://github.com/emendir/WalytisTechnologies/blob/master/Walytis/Meaning/IntroductionToWalytis.md)

**_A flexible, lightweight, nonlinear blockchain, serving as a P2P distributed database._**
_`4D61646520776974682073696E63657265206C6F766520666F72206D616E6B696E642E`_

## Intro

Walytis is a database-blockchain, a type of blockchain that is essentially a fully distributed database-management system.

As a blockchain, it is uniquely lightweight (can run on a smartphone), has a non-linear chain of blocks (allowing simultaneous block creation), and has nothing to do with cryptocurrencies or tokenomics.
There is no single universal instance of the Walytis blockchain.
Instead, applications create new Walytis database-blockchains whenever they need one.


## Examples of Applications

Walytis is designed to be used for systems that require peer-to-peer databases.
Here are a few examples of applications that are developed based on Walytis:

- [Messenger](https://github.com/emendir/Endra): A database-blockchain can be used to record the existence of messages in a chatroom. Actual message content is stored off-chain for privacy. In this case the database-blockchain is used not for storage but to help the various devices of the member's chatroom coordinate their data synchronisation.
  
- File Synchronisation: File changes are recorded in blocks, creating a complete unified history of file edits across users. Actual files are stored off-chain for storage-efficiency.
  
- Serverless Git Collaboration: Ever notice that git already looks like a blockchain? Map git commits onto Walytis blocks and git repositories onto Walytis blockchains and you've got a shared git repo!
  
- [Identity Management](https://github.com/emendir/WalytisIdentities): One data-base blockchain is used for every identity, publishing [DID-documents](https://www.w3.org/TR/did-1.0/) as blocks, cryptographically authenticated

## Walytis Technologies SDK

[Walytis Technologies](https://github.com/emendir/WalytisTechnologies) is a collection of tools based on Walytis built to enable developers to easily develop peer-to-peer distributed applications.

It includes [blockchain overlays](#Blockchain%20Overlays) that extend Walytis' capabilities as a database, as well as essential communications systems such as [identity and cryptographic key management](https://github.com/emendir/WalytisIdentities).

### Blockchain Overlays

The features of Walytis blockchains can be expanded by building modules on top of them that provide applications with interfaces to database-blockchains that have unique features and functionality not built into Walytis.
Currently under development are tools for off-chain and encrypted data storage, authentication, access-control, identity-management and mutable data structures 

- [WalytisOffchain](https://github.com/emendir/WalytisOffchain): Secure access-controlled blockchain with off-chain storage, built on [WalytisIdentities](https://github.com/emendir/WalytisIdentities).
- [WalytisMutability](https://github.com/emendir/WalytisMutability): A Walytis blockchain overlay featuring block mutability.

These blockchain overlays are built in a modular way so that application developers can choose which extra features they need for their use case.
These modules can be compounded to combine their features.

## Documentation

To learn how Walytis works, read its documentation, which lives in a dedicated repository:
- https://github.com/emendir/WalytisTechnologies/blob/master/Walytis/DocsOverview.md

Some key entry points to the docs:
- [Introduction to Walytis](https://github.com/emendir/WalytisTechnologies/blob/master/Walytis/Meaning/IntroductionToWalytis.md): Learn to understand Walytis
- [Walytis' Rationale](https://github.com/emendir/WalytisTechnologies/blob/master/Walytis/Meaning/WalytisRationale.md): Learn why Walytis was developed
- [Walytis Tutorials](https://github.com/emendir/WalytisTechnologies/blob/master/Walytis/Tutorials/0-TutorialOverview.md): learn how to build programs that use Walytis
- [walytis_beta_api API reference](./docs/API-Reference/walytis_beta_api/index.html): Python library API reference

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

## Project Status

Walytis is in the beta stage of development.
This means it is fully functional and its programming API is stable, remaining fully backward compatible until it matures out of the beta stage.

## [Roadmap](RoadMap)
- [Walytis RoadMap](RoadMap.md): Roadmap for the development of Walytis
- [Walytis Technologies RoadMap](https://github.com/emendir/WalytisTechnologies/blob/master/RoadMap.md): Roadmap for the broader development of [Walytis Technologies](https://github.com/emendir/WalytisTechnologies/), an SDK of tools based on Walytis for peer-to-peer communications.

## Contributing

### Analysis and Review

If you have any thoughts on Walytis or want to discuss the sensibility of its unique features, feel free to share them under GitHub discussions.

I would especially appreciate reviews and analyses of [Walytis' blockchain-architecture security](https://github.com/emendir/WalytisTechnologies/blob/master/Walytis/Technical/WalytisBlockchainSecurity.md).

### Software Development

Despite the documentation on Walytis' DevOps not being written yet, feel free to submit pull requests via GitHub if you think you know what you're doing.

### Feature Requests and Bug Reports

If you don't have the time to learn how to contribute code directly, feel free to request features or report bugs via GitHub Issues.

### Donations

To support me in my work on this and other projects, you can make donations with the following currencies:

- **Bitcoin:** `BC1Q45QEE6YTNGRC5TSZ42ZL3MWV8798ZEF70H2DG0`
- **Ethereum:** `0xA32C3bBC2106C986317f202B3aa8eBc3063323D4`
- [Credit Card, Debit Card, Bank Transfer, Apple Pay, Google Pay, Revolut Pay)](https://checkout.revolut.com/pay/4e4d24de-26cf-4e7d-9e84-ede89ec67f32)

Donations help me:
- dedicate more time to developing and maintaining open-source projects
- cover costs for IT resources

## About the Developer

This project is developed by a human one-man team, publishing under the name _Emendir_.  
I build open technologies trying to improve our world;
learning, working and sharing under the principle:

> _Freely I have received, freely I give._

Feel welcome to join in with code contributions, discussions, ideas and more!

## Open-Source in the Public Domain

I dedicate this project to the public domain.
It is open source and free to use, share, modify, and build upon without restrictions or conditions.

I make no patent or trademark claims over this project.  

Formally, you may use this project under either the: 
- [MIT No Attribution (MIT-0)](https://choosealicense.com/licenses/mit-0/) or
- [Creative Commons Zero (CC0)](https://choosealicense.com/licenses/cc0-1.0/)
licence at your choice.  

## Related Projects

### [Walytis Technologies](https://github.com/emendir/WalytisTechnologies)

Overarching project comprising the development of Walytis and a collection of tools based on it for real-world peer-to-peer communications.

- [Walytis](https://github.com/emendir/Walytis_Beta): A flexible, lightweight, nonlinear database-blockchain, built on IPFS.
- [WalytisIdentities](https://github.com/emendir/WalytisIdentities): P2P multi-controller cryptographic identity management, built on Walytis.
- [WalytisOffchain](https://github.com/emendir/WalytisOffchain): Secure access-controlled database-blockchain, built on WalytisIdentities.
- [WalytisMutability](https://github.com/emendir/WalytisMutability): A Walytis blockchain overlay featuring block mutability.
- [Endra](https://github.com/emendir/Endra): A P2P encrypted messaging protocol with multiple devices per user, built on Walytis.
- [EndraApp](https://github.com/emendir/EndraApp): A P2P encrypted messenger supporting multiple devices per user, built on Walytis.

### [IPFS](https://ipfs.tech)

A P2P communication and content addressing protocol developed by Protocol Labs.
This is the networking foundation which Walytis builds upon.

### Alternative Technologies

- [OrbitDB](https://orbitdb.org/): a distributed IPFS-based database written in go
