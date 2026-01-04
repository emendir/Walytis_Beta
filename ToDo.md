### Core

- [ ] Make `walytis_beta_api` capable of fully verifying a blockchain from block data files, so that the role of Walytis Core is only creating and sharing blocks.
- [ ] Join Blockchain timeout when no data has been received during file transmission
- [ ] Remove `block_records` block index? Make more efficient?
- [ ] clean up threads from failed join requests
- [ ] Walytis.get_blockchain_data: tests & documentation
- [ ] auto tests for scaling - 1000 blocks ⏫ 
- [ ] find out how block with 0 parents can be created
- [ ] survive IPFS daemon restarts
- [ ] Joining: replace delay with transmission retry (see TODO comment, probably fix in `ipfs_tk`)
- [ ] walytis_beta_embedded: check if double-import of ipfs node in `.walytis_beta_tools` & `walytis_beta_tools` is a problem


### API
- [ ] GenericBlockchain: add abstract method `set_block_received_handler`?
- [ ] check on efficiency of `walytis_api.Blockchain._load_missed_blocks` amount parameter
- [ ] proper error message when IPFS is turned off
- [ ] Blockchain only remembers if user's block handler processed the block if update_blockids_before_handling == False
- [ ] Blockchain: replace `auto_load_missed_blocks` with `auto_start_block_handling`
- [ ] add replacement for `get_latest_blocks` which automatically uses long IDs
- [ ] deprecate `get_and_read_block` & `read_block`
- [ ] walytis_beta_api.walytis_beta_generic_interface: create tempdir in appdata
- [ ] finish implementation of walytis_beta_embedded (missing functions such as read_block)
- [ ] move value checking and blockchain existence checking logic from walytis_beta_embedded_api & walytis_beta_brethy_api to walytis_beta_generic_interface
- [ ] fix environment variables for Walytis & IPFS-Toolkit and make a stable feature
### Tests

- [ ] test all security functionality
- [ ] test for performance metrics
- [ ] find out scalability limits, expand and test them
- [ ] for all essential tests, make them docker-only (remove role of the calling computer) #phase5

### Security

- [ ] blacklist/whitelisting options in API
- [ ] spam filters: disconnect from and blacklist nodes spamming on:
	- [ ] PubSub listener
	- [ ] join request listener
- [ ] forgery detection system for detecting composed lineages for achieving duplicate hashes

## Docs

- [ ] make structure of API-reference more helpful
	- [ ] then link to the API-reference in pyproject.toml and other places
