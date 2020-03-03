import warnings
warnings.simplefilter(action="ignore", category=FutureWarning)

from web3 import Web3 	# Load basic node framework
from pandas.io.json import json_normalize

import pandas as pd
import sys
import os




### CONTROL PANEL ###
database = "raiden-datacollector-export.csv"
rebuild_database = False  # Create a new csv or add to an existing csv
use_local_node = True  # Use local node or Infura service
force_small_jumps = False  # Force to use small jumps
use_testnet = False  # Use Goerli testnet to gather data - not allowed to be used with mainnet databases because of lack of error handling integration
print_block_range = True  # Print details on progress
debug = False  # Print additional details on data
node = Web3(Web3.HTTPProvider("http://127.0.0.1:8545", request_kwargs={"timeout": 600}))  # Local node path, provide SSH forwarded port on Ethereum node




### LOAD SECRETS FROM ENVIRONMENT FILE - OR OVERRIDE HARDCODED HERE ###
from dotenv import load_dotenv
from pathlib import Path  # Python3 only
env_path = Path('.') / 'raiden-datacollector.env'
load_dotenv(dotenv_path=env_path)

WEB3_INFURA_PROJECT_ID = os.getenv("WEB3_INFURA_PROJECT_ID")  # Import Infura remote node credentials from .env file
WEB3_INFURA_API_SECRET = os.getenv("WEB3_INFURA_API_SECRET")  # Import Infura remote node credentials from .env file




### DEFINITIONS ###
def main():
	print("STARTING UP ...")
	
	connect_node()
	import_database()

	set_raiden()
	download_raiden()

	export_data()
	
	print("\nSHUTTING DOWN ...")

	pass


def	export_data():
	print("\nDATABASE:\nExporting Database ...")

	global df

	df = df.sort_values(by=["Event", "Block"], inplace=False)
	df = df.drop_duplicates(subset=["Block", "Event", "Channel_ID"], keep="last", inplace=False)

	df["Participant_1_Settle_Amount"] = df["Participant_1_Settle_Amount"].astype("Int64")
	df["Participant_1_Settle_Amount"] = df["Participant_1_Settle_Amount"].astype("Int64")
	df["Channel_Amount"] = df["Channel_Amount"].astype("Int64")

	export_csv = df.to_csv(database, index=None, header=True)
	print(">>> SUCCESS: Database exported to:", database, "<<<")

	pass


def download_raiden_channel_settled():
	print("\nChannelSettled() EVENTS:")

	global df

	entries = []

	if not rebuild_database:
		df_temp = df.groupby(["Event"], sort=False)
		df_temp = get_group(df_temp["Block"],"ChannelSettled")

		if not df_temp.empty: first_block = (df.groupby(["Event"], sort=False)["Block"].max())["ChannelSettled"]+1
		else: first_block = contract_deployment
	else: first_block = contract_deployment

	for i in range(first_block, latest_block, jump_width):
		if print_block_range: print("Checking ... ChannelSettled() Block: ", i, "-", i+jump_width)
		
		event_filter = contract.events.ChannelSettled().createFilter(fromBlock=i, toBlock=i+jump_width) # Create filter for block range
		loop_entries = event_filter.get_all_entries() # Get all entries from filter for block range

		if loop_entries:
			entries = entries + loop_entries

	if entries: 
		df_txs = json_normalize(entries) # Import all entries into dataframe
		df_args = json_normalize(df_txs.args) # Import all arguments into dataframe

		df_txs = df_txs.drop(columns=["address", "args", "blockHash", "logIndex", "transactionIndex"])
		if use_testnet: df_args = df_args.drop(columns=["participant1_locksroot", "participant2_locksroot"]) # Balance_Hash and Lockroot Goerli Testnet Contract

		df_temp = df_txs.join(df_args)
		df_temp = df_temp.rename(columns={"blockNumber": "Block", "event": "Event", "channel_identifier": "Channel_ID", "transactionHash": "Transaction", "participant1_amount": "Participant_1_Settle_Amount", "participant2_amount": "Participant_2_Settle_Amount"})
		
		df_temp.Transaction = df_temp.Transaction.apply(lambda x: node.toHex(x))
		df_temp["Network_ID"] = "RDN"

		if use_testnet: df_temp["Network_Type"] = "Testnet"
		else: df_temp["Network_Type"] = "Mainnet"

		if debug:
			print("DF TEMP", df_temp)
			print("DF TEMP COLUMNS", df_temp.columns.values)
			print("DF", df)
			print("DF COLUMNS", df.columns.values)
		
		df = df.append(df_temp, sort=False)
	
		if debug:
			print("DF NEW", df)
			print("DF NEW COLUMNS", df.columns.values)

		print("\nENTRIES:\n", df)
	else:
		print("No entries found!\n")

	pass


def download_raiden_new_deposit():
	print("\nChannelNewDeposit() EVENTS:")

	global df

	entries = []

	if not rebuild_database:
		df_temp = df.groupby(["Event"], sort=False)
		df_temp = get_group(df_temp["Block"],"ChannelNewDeposit")

		if not df_temp.empty: first_block = (df.groupby(["Event"], sort=False)["Block"].max())["ChannelNewDeposit"]+1
		else: first_block = contract_deployment
	else: first_block = contract_deployment

	for i in range(first_block, latest_block, jump_width):
		if print_block_range: print("Checking ... ChannelNewDeposit() Block: ", i, "-", i+jump_width)
		
		event_filter = contract.events.ChannelNewDeposit().createFilter(fromBlock=i, toBlock=i+jump_width) # Create filter for block range
		loop_entries = event_filter.get_all_entries() # Get all entries from filter for block range

		if loop_entries:
			entries = entries + loop_entries

	if entries: 
		df_txs = json_normalize(entries) # Import all entries into dataframe
		df_args = json_normalize(df_txs.args) # Import all arguments into dataframe

		df_txs = df_txs.drop(columns=["address", "args", "blockHash", "logIndex", "transactionIndex"])
		
		df_temp = df_txs.join(df_args)
		df_temp = df_temp.rename(columns={"blockNumber": "Block", "event": "Event", "channel_identifier": "Channel_ID", "transactionHash": "Transaction", "participant": "Channel_Participant_1", "total_deposit": "Channel_Amount"})
		
		df_temp.Transaction = df_temp.Transaction.apply(lambda x: node.toHex(x))
		df_temp["Network_ID"] = "RDN"

		if use_testnet: df_temp["Network_Type"] = "Testnet"
		else: df_temp["Network_Type"] = "Mainnet"

		if debug:
			print("DF TEMP", df_temp)
			print("DF TEMP COLUMNS", df_temp.columns.values)
			print("DF", df)
			print("DF COLUMNS", df.columns.values)
		
		df = df.append(df_temp, sort=False)
	
		if debug:
			print("DF NEW", df)
			print("DF NEW COLUMNS", df.columns.values)

		print("\nENTRIES:\n", df)
	else:
		print("No entries found!\n")

	pass


def download_raiden_channel_closed():
	print("\nChannelClosed() EVENTS:")

	global df

	entries = []

	if not rebuild_database:
		df_temp = df.groupby(["Event"], sort=False)
		df_temp = get_group(df_temp["Block"],"ChannelClosed")

		if not df_temp.empty: first_block = (df.groupby(["Event"], sort=False)["Block"].max())["ChannelClosed"]+1
		else: first_block = contract_deployment
	else: first_block = contract_deployment

	for i in range(first_block, latest_block, jump_width):
		if print_block_range: print("Checking ... ChannelClosed() Block: ", i, "-", i+jump_width)
		
		event_filter = contract.events.ChannelClosed().createFilter(fromBlock=i, toBlock=i+jump_width) # Create filter for block range
		loop_entries = event_filter.get_all_entries() # Get all entries from filter for block range

		if loop_entries:
			entries = entries + loop_entries
			
	if entries: 
		df_txs = json_normalize(entries) # Import all entries into dataframe
		df_args = json_normalize(df_txs.args) # Import all arguments into dataframe

		df_txs = df_txs.drop(columns=["address", "args", "blockHash", "logIndex", "transactionIndex"])
		
		if use_testnet: df_args = df_args.drop(columns=["nonce", "balance_hash"]) # Drop balance_hash and lockroot on Goerli testnet contract
		else: df_args = df_args.drop(columns=["nonce"])
		
		df_temp = df_txs.join(df_args)
		df_temp = df_temp.rename(columns={"blockNumber": "Block", "event": "Event", "channel_identifier": "Channel_ID", "transactionHash": "Transaction", "closing_participant": "Channel_Participant_1"})
		
		df_temp.Transaction = df_temp.Transaction.apply(lambda x: node.toHex(x))
		df_temp["Network_ID"] = "RDN"

		if use_testnet: df_temp["Network_Type"] = "Testnet"
		else: df_temp["Network_Type"] = "Mainnet"

		if debug:
			print("DF TEMP", df_temp)
			print("DF TEMP COLUMNS", df_temp.columns.values)
			print("DF", df)
			print("DF COLUMNS", df.columns.values)
		
		df = df.append(df_temp, sort=False)
	
		if debug:
			print("DF NEW", df)
			print("DF NEW COLUMNS", df.columns.values)

		print("\nENTRIES:\n", df)
	else:
		print("No entries found!\n")

	pass


def	download_raiden_channel_opened():
	print("ChannelOpened() EVENTS:")

	global df

	entries = []

	if not rebuild_database:
		df_temp = df.groupby(["Event"], sort=False)
		df_temp = get_group(df_temp["Block"],"ChannelOpened")

		if not df_temp.empty: first_block = (df.groupby(["Event"], sort=False)["Block"].max())["ChannelOpened"]+1
		else: first_block = contract_deployment
	else: first_block = contract_deployment

	for i in range(first_block, latest_block, jump_width):
		if print_block_range: print("Checking ... ChannelOpened() Block: ", i, "-", i+jump_width)
		
		event_filter = contract.events.ChannelOpened().createFilter(fromBlock=i, toBlock=i+jump_width) # Create filter for block range
		loop_entries = event_filter.get_all_entries() # Get all entries from filter for block range

		if loop_entries:
			entries = entries + loop_entries

	if entries: 
		df_txs = json_normalize(entries) # Import all entries into dataframe
		df_args = json_normalize(df_txs.args) # Import all arguments into dataframe

		df_txs = df_txs.drop(columns=["address", "args", "blockHash", "logIndex", "transactionIndex"])
		df_args = df_args.drop(columns=["settle_timeout"])
		
		df_temp = df_txs.join(df_args)
		df_temp = df_temp.rename(columns={"blockNumber": "Block", "event": "Event", "channel_identifier": "Channel_ID", "transactionHash": "Transaction", "participant1": "Channel_Participant_1", "participant2": "Channel_Participant_2"})
		
		df_temp.Transaction = df_temp.Transaction.apply(lambda x: node.toHex(x))
		df_temp["Network_ID"] = "RDN"

		if use_testnet: df_temp["Network_Type"] = "Testnet"
		else: df_temp["Network_Type"] = "Mainnet"

		if debug:
			print("\nDF TEMP", df_temp)
			print("\nDF TEMP COLUMNS", df_temp.columns.values)
			print("\nDF", df)
			print("\nDF COLUMNS", df.columns.values)
		
		df = df.append(df_temp, sort=False)

		if debug:
			print("\nDF NEW", df)
			print(df.columns.values)
		print("\nENTRIES:\n", df)
	else:
		print("No entries found!\n")

	pass


def get_group(g, key):
	if key in g.groups: return g.get_group(key) # To catch key error with default value, groupby cannot handle it when name does not exist
	
	return pd.DataFrame()


def	download_raiden():
	print("\nLOADING RAIDEN:")
	download_raiden_channel_opened()
	download_raiden_channel_closed()
	download_raiden_new_deposit()
	download_raiden_channel_settled()

	pass


def set_raiden():
	print("\nSETTING RAIDEN:")

	global contract
	global contract_deployment

	if use_testnet:
		contract_deployment = 1508741  # Goerli contract deployment
		contract_address = "0xDa1fBc048f503635950058953f5c60FC1F564ee6"
		contract_abi = [{"constant":False,"inputs":[{"name":"channel_identifier","type":"uint256"},{"name":"receiver","type":"address"},{"name":"sender","type":"address"},{"name":"locks","type":"bytes"}],"name":"unlock","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[{"name":"participant1","type":"address"},{"name":"participant2","type":"address"},{"name":"settle_timeout","type":"uint256"}],"name":"openChannel","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[],"name":"deprecate","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"settlement_timeout_max","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"deprecation_executor","outputs":[{"name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"secret_registry","outputs":[{"name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"chain_id","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"token_network_deposit_limit","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"","type":"bytes32"}],"name":"participants_hash_to_channel_identifier","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"channel_participant_deposit_limit","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"channel_identifier","type":"uint256"},{"name":"participant","type":"address"},{"name":"total_deposit","type":"uint256"},{"name":"partner","type":"address"}],"name":"setTotalDeposit","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"channel_counter","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"MAX_SAFE_UINT256","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"contract_address","type":"address"}],"name":"contractExists","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"participant","type":"address"},{"name":"partner","type":"address"}],"name":"getParticipantsHash","outputs":[{"name":"","type":"bytes32"}],"payable":False,"stateMutability":"pure","type":"function"},{"constant":False,"inputs":[{"name":"channel_identifier","type":"uint256"},{"name":"non_closing_participant","type":"address"},{"name":"closing_participant","type":"address"},{"name":"balance_hash","type":"bytes32"},{"name":"nonce","type":"uint256"},{"name":"additional_hash","type":"bytes32"},{"name":"non_closing_signature","type":"bytes"},{"name":"closing_signature","type":"bytes"}],"name":"closeChannel","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[{"name":"channel_identifier","type":"uint256"},{"name":"participant1","type":"address"},{"name":"participant2","type":"address"}],"name":"getChannelInfo","outputs":[{"name":"","type":"uint256"},{"name":"","type":"uint8"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"signature_prefix","outputs":[{"name":"","type":"string"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"participant","type":"address"},{"name":"partner","type":"address"}],"name":"getChannelIdentifier","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"channel_identifier","type":"uint256"},{"name":"participant1","type":"address"},{"name":"participant1_transferred_amount","type":"uint256"},{"name":"participant1_locked_amount","type":"uint256"},{"name":"participant1_locksroot","type":"bytes32"},{"name":"participant2","type":"address"},{"name":"participant2_transferred_amount","type":"uint256"},{"name":"participant2_locked_amount","type":"uint256"},{"name":"participant2_locksroot","type":"bytes32"}],"name":"settleChannel","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[{"name":"channel_identifier","type":"uint256"},{"name":"participant","type":"address"},{"name":"total_withdraw","type":"uint256"},{"name":"expiration_block","type":"uint256"},{"name":"participant_signature","type":"bytes"},{"name":"partner_signature","type":"bytes"}],"name":"setTotalWithdraw","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"safety_deprecation_switch","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"settlement_timeout_min","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"","type":"uint256"}],"name":"channels","outputs":[{"name":"settle_block_number","type":"uint256"},{"name":"state","type":"uint8"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"channel_identifier","type":"uint256"},{"name":"participant","type":"address"},{"name":"partner","type":"address"}],"name":"getChannelParticipantInfo","outputs":[{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"bool"},{"name":"","type":"bytes32"},{"name":"","type":"uint256"},{"name":"","type":"bytes32"},{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"channel_identifier","type":"uint256"},{"name":"closing_participant","type":"address"},{"name":"non_closing_participant","type":"address"},{"name":"balance_hash","type":"bytes32"},{"name":"nonce","type":"uint256"},{"name":"additional_hash","type":"bytes32"},{"name":"closing_signature","type":"bytes"},{"name":"non_closing_signature","type":"bytes"}],"name":"updateNonClosingBalanceProof","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"token","outputs":[{"name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"channel_identifier","type":"uint256"},{"name":"sender","type":"address"},{"name":"receiver","type":"address"}],"name":"getUnlockIdentifier","outputs":[{"name":"","type":"bytes32"}],"payable":False,"stateMutability":"pure","type":"function"},{"inputs":[{"name":"_token_address","type":"address"},{"name":"_secret_registry","type":"address"},{"name":"_chain_id","type":"uint256"},{"name":"_settlement_timeout_min","type":"uint256"},{"name":"_settlement_timeout_max","type":"uint256"},{"name":"_deprecation_executor","type":"address"},{"name":"_channel_participant_deposit_limit","type":"uint256"},{"name":"_token_network_deposit_limit","type":"uint256"}],"payable":False,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":False,"inputs":[{"indexed":True,"name":"channel_identifier","type":"uint256"},{"indexed":True,"name":"participant1","type":"address"},{"indexed":True,"name":"participant2","type":"address"},{"indexed":False,"name":"settle_timeout","type":"uint256"}],"name":"ChannelOpened","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"channel_identifier","type":"uint256"},{"indexed":True,"name":"participant","type":"address"},{"indexed":False,"name":"total_deposit","type":"uint256"}],"name":"ChannelNewDeposit","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"name":"new_value","type":"bool"}],"name":"DeprecationSwitch","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"channel_identifier","type":"uint256"},{"indexed":True,"name":"participant","type":"address"},{"indexed":False,"name":"total_withdraw","type":"uint256"}],"name":"ChannelWithdraw","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"channel_identifier","type":"uint256"},{"indexed":True,"name":"closing_participant","type":"address"},{"indexed":True,"name":"nonce","type":"uint256"},{"indexed":False,"name":"balance_hash","type":"bytes32"}],"name":"ChannelClosed","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"channel_identifier","type":"uint256"},{"indexed":True,"name":"receiver","type":"address"},{"indexed":True,"name":"sender","type":"address"},{"indexed":False,"name":"locksroot","type":"bytes32"},{"indexed":False,"name":"unlocked_amount","type":"uint256"},{"indexed":False,"name":"returned_tokens","type":"uint256"}],"name":"ChannelUnlocked","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"channel_identifier","type":"uint256"},{"indexed":True,"name":"closing_participant","type":"address"},{"indexed":True,"name":"nonce","type":"uint256"},{"indexed":False,"name":"balance_hash","type":"bytes32"}],"name":"NonClosingBalanceProofUpdated","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"channel_identifier","type":"uint256"},{"indexed":False,"name":"participant1_amount","type":"uint256"},{"indexed":False,"name":"participant1_locksroot","type":"bytes32"},{"indexed":False,"name":"participant2_amount","type":"uint256"},{"indexed":False,"name":"participant2_locksroot","type":"bytes32"}],"name":"ChannelSettled","type":"event"}]
		print("Smart Contract deployed on: Goerli Testnet")
	else:
		contract_deployment = 6532988  # Mainnet contract deployment
		contract_address = "0xa5C9ECf54790334B73E5DfA1ff5668eB425dC474"
		contract_abi = [{"constant":False,"inputs":[{"name":"channel_identifier","type":"uint256"},{"name":"participant","type":"address"},{"name":"partner","type":"address"},{"name":"merkle_tree_leaves","type":"bytes"}],"name":"unlock","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[{"name":"participant1","type":"address"},{"name":"participant2","type":"address"},{"name":"settle_timeout","type":"uint256"}],"name":"openChannel","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[],"name":"deprecate","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"settlement_timeout_max","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"deprecation_executor","outputs":[{"name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"secret_registry","outputs":[{"name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"chain_id","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"token_network_deposit_limit","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"","type":"bytes32"}],"name":"participants_hash_to_channel_identifier","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"channel_participant_deposit_limit","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"channel_identifier","type":"uint256"},{"name":"participant","type":"address"},{"name":"total_deposit","type":"uint256"},{"name":"partner","type":"address"}],"name":"setTotalDeposit","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"channel_counter","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"MAX_SAFE_UINT256","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"contract_address","type":"address"}],"name":"contractExists","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"participant","type":"address"},{"name":"partner","type":"address"}],"name":"getParticipantsHash","outputs":[{"name":"","type":"bytes32"}],"payable":False,"stateMutability":"pure","type":"function"},{"constant":True,"inputs":[{"name":"channel_identifier","type":"uint256"},{"name":"participant1","type":"address"},{"name":"participant2","type":"address"}],"name":"getChannelInfo","outputs":[{"name":"","type":"uint256"},{"name":"","type":"uint8"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"signature_prefix","outputs":[{"name":"","type":"string"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"participant","type":"address"},{"name":"partner","type":"address"}],"name":"getChannelIdentifier","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"channel_identifier","type":"uint256"},{"name":"participant1","type":"address"},{"name":"participant1_transferred_amount","type":"uint256"},{"name":"participant1_locked_amount","type":"uint256"},{"name":"participant1_locksroot","type":"bytes32"},{"name":"participant2","type":"address"},{"name":"participant2_transferred_amount","type":"uint256"},{"name":"participant2_locked_amount","type":"uint256"},{"name":"participant2_locksroot","type":"bytes32"}],"name":"settleChannel","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"contract_version","outputs":[{"name":"","type":"string"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"safety_deprecation_switch","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"settlement_timeout_min","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"channel_identifier","type":"uint256"},{"name":"partner","type":"address"},{"name":"balance_hash","type":"bytes32"},{"name":"nonce","type":"uint256"},{"name":"additional_hash","type":"bytes32"},{"name":"signature","type":"bytes"}],"name":"closeChannel","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[{"name":"","type":"uint256"}],"name":"channels","outputs":[{"name":"settle_block_number","type":"uint256"},{"name":"state","type":"uint8"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"channel_identifier","type":"uint256"},{"name":"participant","type":"address"},{"name":"partner","type":"address"}],"name":"getChannelParticipantInfo","outputs":[{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"bool"},{"name":"","type":"bytes32"},{"name":"","type":"uint256"},{"name":"","type":"bytes32"},{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"channel_identifier","type":"uint256"},{"name":"closing_participant","type":"address"},{"name":"non_closing_participant","type":"address"},{"name":"balance_hash","type":"bytes32"},{"name":"nonce","type":"uint256"},{"name":"additional_hash","type":"bytes32"},{"name":"closing_signature","type":"bytes"},{"name":"non_closing_signature","type":"bytes"}],"name":"updateNonClosingBalanceProof","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"token","outputs":[{"name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"channel_identifier","type":"uint256"},{"name":"participant","type":"address"},{"name":"partner","type":"address"}],"name":"getUnlockIdentifier","outputs":[{"name":"","type":"bytes32"}],"payable":False,"stateMutability":"pure","type":"function"},{"inputs":[{"name":"_token_address","type":"address"},{"name":"_secret_registry","type":"address"},{"name":"_chain_id","type":"uint256"},{"name":"_settlement_timeout_min","type":"uint256"},{"name":"_settlement_timeout_max","type":"uint256"},{"name":"_deprecation_executor","type":"address"}],"payable":False,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":False,"inputs":[{"indexed":True,"name":"channel_identifier","type":"uint256"},{"indexed":True,"name":"participant1","type":"address"},{"indexed":True,"name":"participant2","type":"address"},{"indexed":False,"name":"settle_timeout","type":"uint256"}],"name":"ChannelOpened","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"channel_identifier","type":"uint256"},{"indexed":True,"name":"participant","type":"address"},{"indexed":False,"name":"total_deposit","type":"uint256"}],"name":"ChannelNewDeposit","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"channel_identifier","type":"uint256"},{"indexed":True,"name":"closing_participant","type":"address"},{"indexed":True,"name":"nonce","type":"uint256"}],"name":"ChannelClosed","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"channel_identifier","type":"uint256"},{"indexed":True,"name":"participant","type":"address"},{"indexed":True,"name":"partner","type":"address"},{"indexed":False,"name":"locksroot","type":"bytes32"},{"indexed":False,"name":"unlocked_amount","type":"uint256"},{"indexed":False,"name":"returned_tokens","type":"uint256"}],"name":"ChannelUnlocked","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"channel_identifier","type":"uint256"},{"indexed":True,"name":"closing_participant","type":"address"},{"indexed":True,"name":"nonce","type":"uint256"}],"name":"NonClosingBalanceProofUpdated","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"channel_identifier","type":"uint256"},{"indexed":False,"name":"participant1_amount","type":"uint256"},{"indexed":False,"name":"participant2_amount","type":"uint256"}],"name":"ChannelSettled","type":"event"}]
		print("Smart Contract deployed on: Mainnet")
		
	contract = node.eth.contract(address=contract_address, abi=contract_abi)

	print("Deployment block number:", contract_deployment)
	print("Contract address:", contract_address)

	pass


def import_database():
	print("\nDATABASE:\nRebuilding Database ...", rebuild_database)

	global df
	global latest_block

	if rebuild_database:
		df = pd.DataFrame(columns = ["Block", "Event", "Network_ID", "Network_Type", "Token_ID", "Channel_Amount", "Participant_1_Settle_Amount", "Participant_2_Settle_Amount", "Channel_ID", "Transaction", "Channel_Participant_1", "Channel_Participant_2"])
		
		export_csv = df.to_csv(database, index=None, header=True)
		if debug: print("Created Database:", database)

	try: probe = df = pd.read_csv(database, index_col=False)
	except: raise Exception("\n\n\n>>> ABORT: Database does not exist. Check if correct path is set or set rebuild_database = True <<<\n\n\n\n\n")

	print("Loaded Database:", database)

	if debug: print("\n", df)

	if not rebuild_database:
		probe = df["Network_Type"].values[1]
		
		if use_testnet and probe=="Mainnet": sys.exit("\n\n\n>>> ABORT: Mainnet & Testnet Database crossover prevented <<<\n\n\n\n\n")
		if not use_testnet and probe=="Testnet": sys.exit("\n\n\n>>> ABORT: Mainnet & Testnet Database crossover prevented <<<\n\n\n\n\n")

	pass


def switch_to_testnet():
	global node

	if not use_local_node:
		print("Switching to Testnet ...", use_testnet)
		from web3.auto.infura.goerli import w3 as node # overwrite node
		node.provider.websocket_timeout = 600
	else:
		sys.exit("\n>>> ABORT: Goerli Testnet not integrated on Sparkmaster <<<\n\n\n\n\n")

	pass


def switch_to_remote_node():
	print("Infura PROJECT_ID: ", os.environ["WEB3_INFURA_PROJECT_ID"])
	print("Infura API SECRET: ", os.environ["WEB3_INFURA_API_SECRET"])

	global node

	from web3.auto.infura import w3 as node # overwrite node
	node.provider.websocket_timeout = 600

	print("Switching to remote node ...", not use_local_node)

	pass


def connect_node():
	print("\nNODE STATS:")

	if not use_local_node: switch_to_remote_node()

	if use_testnet: switch_to_testnet()

	global latest_block
	global jump_width

	connection = node.isConnected()
	syncing = node.eth.syncing

	latest_block =  node.eth.blockNumber

	if force_small_jumps: jump_width = 1000
	elif not use_local_node and not use_testnet: jump_width = 100000 # Should work most of the time, could timeout at times at Infura
	elif not rebuild_database: jump_width = 100000 # Should work all the time to fetch all in big blocks, newer events were tested unproblematic to timeout issues
	else: jump_width = 1000

	print("Node connected  ...", connection)
	print("Node still syncing ...", syncing)
	print("Latest block number:", latest_block)
	if debug: print("Latest Block: getBlock(): \n", node.eth.getBlock("latest"))

	pass


### APPLICATION ENTRY POINT ###
main()