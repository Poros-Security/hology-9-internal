import importlib.util
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


sys.modules.setdefault(
    "sandbox",
    SimpleNamespace(run_launcher=lambda *args, **kwargs: None),
)

spec = importlib.util.spec_from_file_location(
    "jackpotto_chal", Path(__file__).with_name("chal.py")
)
chal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chal)


class FakeConstructor:
    def __init__(self, transaction):
        self.transaction = transaction

    def build_transaction(self, transaction):
        self.transaction.update(transaction)
        return self.transaction


class FakeContract:
    def __init__(self, transaction):
        self.transaction = transaction

    def constructor(self):
        return FakeConstructor(self.transaction)


class FakeEth:
    def __init__(self, receipt):
        self.receipt = receipt
        self.transaction = {}
        self.account = SimpleNamespace(
            sign_transaction=lambda transaction, private_key: SimpleNamespace(
                raw_transaction=b"signed"
            )
        )

    def contract(self, abi, bytecode):
        return FakeContract(self.transaction)

    def get_transaction_count(self, address):
        return 0

    def send_raw_transaction(self, raw_transaction):
        return b"hash"

    def wait_for_transaction_receipt(self, transaction_hash):
        return self.receipt


class FakeWeb3:
    def __init__(self, receipt):
        self.eth = FakeEth(receipt)
        self.provider = SimpleNamespace(
            endpoint_uri="http://localhost:8545",
            make_request=lambda method, params: {"result": True},
        )


class DeployTests(unittest.TestCase):
    def setUp(self):
        contract_artifact = json.dumps(
            {'abi': [], 'bytecode': {'object': '0x00'}}
        )
        artifact_patch = patch.object(
            chal.Path, 'read_text', return_value=contract_artifact
        )
        artifact_patch.start()
        self.addCleanup(artifact_patch.stop)

    def test_deployment_includes_gas_headroom(self):
        web3 = FakeWeb3(SimpleNamespace(status=1, contractAddress="0xsetup"))

        address = chal.deploy(web3, "0xdeployer", "0xkey", "0xplayer")

        self.assertEqual(address, "0xsetup")
        self.assertGreaterEqual(web3.eth.transaction["gas"], 1_000_000)

    def test_failed_deployment_does_not_return_a_null_address(self):
        web3 = FakeWeb3(SimpleNamespace(status=0, contractAddress=None))

        with self.assertRaisesRegex(RuntimeError, "deployment transaction failed"):
            chal.deploy(web3, "0xdeployer", "0xkey", "0xplayer")


if __name__ == "__main__":
    unittest.main()
