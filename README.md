# Raiden Datacollector

A python script that collects on-chain channel data from the Raiden Network.

This script was programmed to serve a master's thesis covering blockchain data analysis. Its aim is to fetch available on-chain channel data about the Ethereum-based second layer network Raiden and export the channel information into a .csv database. It mainly uses a Web3-interface and the pandas library to fetch and sort channel information and can rely on remote or local Ethereum clients for connections to the network.


## Getting Started

These instructions will get you a copy of the project up and running on your local machine.


### Prerequisites

It is *highly recommmended* to install this software freshly into a [minimal environment](https://web3py.readthedocs.io/en/stable/troubleshooting.html#setup-environment) because experience has shown that web3.py interacts with other packages unexpectedly at times. A Miniconda installation has proven to be sufficient and can be found [here](https://docs.conda.io/en/latest/miniconda.html).

```
# Create an empty environment with name myenv
conda create -n myenv python

# Activate the environment
conda activate myenv

# Update Python to a current version
conda update python
```

A synchronized Ethereum full node with the latest [go-ethereum (GETH) client](https://github.com/ethereum/go-ethereum) is needed for use of a local node, callable via SSH to HTTP socket. An [Infura account](https://infura.io/) is needed for using a remote node.

Required Software packages

```
python 3.6
web3 5.2.2
pandas 1.0.1
dotenv 0.12
geth current version with client synced (for local node)
Infura account (for remote node)
```

### Installing

Make sure you have a clean environment to install the web3.py package, if not already installed. Activate the environment, if not already done. Install the web3.py package via pip or another method outlined [here](https://web3py.readthedocs.io/en/stable/quickstart.html#installation).

```
# With virtualenv active, make sure you have the latest packaging tools
pip install --upgrade pip setuptools

# Now we can install web3.py
pip install --upgrade web3
```

Install pandas package via pip or another method outlined [here](https://pandas.pydata.org/docs/getting_started/install.html). Add a [dotenv](https://pypi.org/project/python-dotenv/) package via pip.

```
# Install pandas package with conda or pip command
conda install pandas

# Install dotenv package
pip install -U python-dotenv
```

## Deployment

Clone the project on your deployment system of choice.

Edit the *raiden-datacollector.env-template* file by editing your Infura credentials and save the file as *raiden-datacollector.env* if the Infura remote node is used.

```
# Insert your credentials here
WEB3_INFURA_PROJECT_ID = "abcef"
WEB3_INFURA_API_SECRET = "ghijk"
```

If a local node is used, *point an SSH tunnel to port 8545* to your node bearing system via *shell command*. Make sure the port is reachable. 

```
# Point this to your target system
ssh -N -v user@192.168.1.2 -L 8545:localhost:8545
```

Provide a reasonable timeout of 5 minutes or more on the node bearing system, if possible. There are blocks in the range of *8990000-900000* which take a long time to read and can trigger timouts. The script is adapting jump width as good as possible. This might need further readjustment depending on deployment details.

Edit the flags  in the beginning of the Python script.

* *database (string)*; this string specifies the destination for the .csv database, for either creating a new one or adding to an existing one
* *rebuild_database (boolean)*; this flag specifies if a new database is to be created or adding to an existing one 
* *use_local_node (boolean)*; this flag specifies if a local tunnel is used or an Infura remote node
* *force_small_jumps (boolean)*; this flag is forcing small jumps, if not set
* *use_testnet (boolean)*; this flag is setting the target network to either the Ethereum mainnet or the Goerli testnet. The script is not designed to build a database containing both
* *print_block_range (boolean)*; this flag prints the block range called, to gauge progress
* *debug (boolean)*; this flag prints additional info about the data retrieved, for debugging data frames after new implementations
* *node (string)*; this string specifies the local node path. Please provide an SSH forwarded port to the local Ethereum node via shell command or script

```
### CONTROL PANEL ###
database = "raiden-datacollector-export.csv"
rebuild_database = False  # Create a new csv or add to an existing csv
use_local_node = False  # Use local node or Infura service
force_small_jumps = False  # Force to use small jumps
use_testnet = False  # Use Goerli testnet to gather data - not allowed to be used with mainnet databases because of lack of error handling integration
print_block_range = True  # Print details on progress
debug = False  # Print additional details on data
node = Web3(Web3.HTTPProvider("http://127.0.0.1:8545", request_kwargs={"timeout": 600}))  # Local node path, provide SSH forwarded port on Ethereum node
```

You can override or omit the .env file and hardcode the credentials into the following part of the script, which is not recommended to prevent accidental deployment of credentials.

```
# Change these credentials
WEB3_INFURA_PROJECT_ID = os.getenv("WEB3_INFURA_PROJECT_ID")  # Import Infura remote node credentials from .env file
WEB3_INFURA_API_SECRET = os.getenv("WEB3_INFURA_API_SECRET")  # Import Infura remote node credentials from .env file

# to that, containing your credentials
WEB3_INFURA_PROJECT_ID = "abcef"
WEB3_INFURA_API_SECRET = "ghijk"
```

The on-chain Raiden channel data will now be exported into the specified .csv database. If the *rebuild_database* flag is set to false, only additional data since the last recorded events are downloaded with running the script. This is recommended for continous deployment.

A successful run of the script, adding to an existing database will look like this:

```
STARTING UP ...

NODE STATS:
Infura PROJECT_ID:  abcef
Infura API SECRET:  ghijk
Switching to remote node ... True
Node connected  ... True
Node still syncing ... False
Latest block number: 9637510

DATABASE:
Rebuilding Database ... False
Loaded Database: raiden-datacollector-export.csv

SETTING RAIDEN:
Smart Contract deployed on: Mainnet
Deployment block number: 6532988
Contract address: 0xa5C9ECf54790334B73E5DfA1ff5668eB425dC474

LOADING RAIDEN:
ChannelOpened() EVENTS:
Checking ... ChannelOpened() Block:  9213883 - 9313883
Checking ... ChannelOpened() Block:  9313883 - 9413883
Checking ... ChannelOpened() Block:  9413883 - 9513883
Checking ... ChannelOpened() Block:  9513883 - 9613883
Checking ... ChannelOpened() Block:  9613883 - 9713883
No entries found!


ChannelClosed() EVENTS:
Checking ... ChannelClosed() Block:  9214311 - 9314311
Checking ... ChannelClosed() Block:  9314311 - 9414311
Checking ... ChannelClosed() Block:  9414311 - 9514311
Checking ... ChannelClosed() Block:  9514311 - 9614311
Checking ... ChannelClosed() Block:  9614311 - 9714311
No entries found!


ChannelNewDeposit() EVENTS:
Checking ... ChannelNewDeposit() Block:  9214235 - 9314235
Checking ... ChannelNewDeposit() Block:  9314235 - 9414235
Checking ... ChannelNewDeposit() Block:  9414235 - 9514235
Checking ... ChannelNewDeposit() Block:  9514235 - 9614235
Checking ... ChannelNewDeposit() Block:  9614235 - 9714235
No entries found!


ChannelSettled() EVENTS:
Checking ... ChannelSettled() Block:  9214355 - 9314355
Checking ... ChannelSettled() Block:  9314355 - 9414355
Checking ... ChannelSettled() Block:  9414355 - 9514355
Checking ... ChannelSettled() Block:  9514355 - 9614355
Checking ... ChannelSettled() Block:  9614355 - 9714355
No entries found!


DATABASE:
Exporting Database ...
>>> SUCCESS: Database exported to: raiden-datacollector-export.csv <<<

SHUTTING DOWN ...
[Finished in 15.8s]
```

Continue with an analysis software of your choice or use the repository raiden-investigator on this github.


## Built With

* [Sublime Text](https://www.sublimetext.com/) - Text editor for development
* [Miniconda](https://docs.conda.io/en/latest/miniconda.html) - Python package manager
* [Sublime Merge](https://www.sublimemerge.com/) - Git client
* [Jupyter Notebook](https://jupyter.org/) - Data science suite


## Authors

**Christian Winter** - *Initial work for master's thesis* - [wintermostly](https://github.com/wintermostly)


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details