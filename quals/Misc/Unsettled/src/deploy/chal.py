import os


# GZCTF injects one flag per team. The launcher reads FLAG during import.
gzctf_flag = os.environ.get("GZCTF_FLAG")
if gzctf_flag:
    os.environ["FLAG"] = gzctf_flag


import json
from pathlib import Path

import sandbox
from web3 import Web3


def set_balance(web3: Web3, account_address: str, amount: int) -> None:
    response = web3.provider.make_request(
        "anvil_setBalance",
        [account_address, amount],
    )
    if "error" in response:
        raise RuntimeError(f"failed to fund player: {response['error']}")


def deploy(
    web3: Web3,
    deployer_address: str,
    deployer_private_key: str,
    player_address: str,
) -> str:
    contract_info = json.loads(
        Path("compiled/Setup.sol/Setup.json").read_text(encoding="utf-8")
    )
    contract = web3.eth.contract(
        abi=contract_info["abi"],
        bytecode=contract_info["bytecode"]["object"],
    )

    deployment_transaction = contract.constructor(player_address).build_transaction(
        {
            "from": deployer_address,
            "nonce": web3.eth.get_transaction_count(deployer_address),
        }
    )
    signed_transaction = web3.eth.account.sign_transaction(
        deployment_transaction,
        deployer_private_key,
    )
    transaction_hash = web3.eth.send_raw_transaction(
        signed_transaction.raw_transaction
    )
    receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)

    if receipt.status != 1 or not receipt.contractAddress:
        raise RuntimeError("deployment transaction failed")

    set_balance(web3, player_address, Web3.to_wei(1, "ether"))
    return receipt.contractAddress


def pre_tx_hook(data, node_info):
    return 200, ""


def post_tx_hook(data, response, node_info):
    return 200, ""


app = sandbox.run_launcher(
    deploy,
    pre_tx_hook=pre_tx_hook,
    post_tx_hook=post_tx_hook,
)
