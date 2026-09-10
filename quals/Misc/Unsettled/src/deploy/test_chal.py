import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


sys.modules.setdefault(
    "sandbox",
    SimpleNamespace(run_launcher=lambda *args, **kwargs: None),
)


def load_challenge_module():
    spec = importlib.util.spec_from_file_location(
        "batch_market_chal", Path(__file__).with_name("chal.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeConstructor:
    def __init__(self, transaction, constructor_args):
        self.transaction = transaction
        self.constructor_args = constructor_args

    def build_transaction(self, transaction):
        self.transaction.update(transaction)
        return self.transaction


class FakeContract:
    def __init__(self, transaction):
        self.transaction = transaction
        self.constructor_args = None

    def constructor(self, *args):
        self.constructor_args = args
        return FakeConstructor(self.transaction, args)


class FakeEth:
    def __init__(self, receipt):
        self.receipt = receipt
        self.transaction = {}
        self.created_contract = None
        self.account = SimpleNamespace(
            sign_transaction=lambda transaction, private_key: SimpleNamespace(
                raw_transaction=b"signed"
            )
        )

    def contract(self, abi, bytecode):
        self.created_contract = FakeContract(self.transaction)
        return self.created_contract

    def get_transaction_count(self, address):
        return 0

    def send_raw_transaction(self, raw_transaction):
        return b"transaction-hash"

    def wait_for_transaction_receipt(self, transaction_hash):
        return self.receipt


class FakeProvider:
    endpoint_uri = "http://localhost:8545"

    def __init__(self):
        self.requests = []

    def make_request(self, method, params):
        self.requests.append((method, params))
        return {"result": True}


class FakeWeb3:
    def __init__(self, receipt):
        self.eth = FakeEth(receipt)
        self.provider = FakeProvider()


class DeployTests(unittest.TestCase):
    def setUp(self):
        self.chal = load_challenge_module()
        contract_artifact = json.dumps(
            {"abi": [], "bytecode": {"object": "0x00"}}
        )
        artifact_patch = patch.object(
            self.chal.Path, "read_text", return_value=contract_artifact
        )
        artifact_patch.start()
        self.addCleanup(artifact_patch.stop)

    def test_deployment_passes_player_to_setup_constructor(self):
        web3 = FakeWeb3(SimpleNamespace(status=1, contractAddress="0xsetup"))

        address = self.chal.deploy(
            web3,
            "0xdeployer",
            "0xdeployer-key",
            "0xplayer",
        )

        self.assertEqual(address, "0xsetup")
        self.assertEqual(web3.eth.created_contract.constructor_args, ("0xplayer",))
        self.assertEqual(
            web3.provider.requests,
            [("anvil_setBalance", ["0xplayer", 10**18])],
        )

    def test_failed_deployment_raises_instead_of_returning_null_address(self):
        web3 = FakeWeb3(SimpleNamespace(status=0, contractAddress=None))

        with self.assertRaisesRegex(RuntimeError, "deployment transaction failed"):
            self.chal.deploy(
                web3,
                "0xdeployer",
                "0xdeployer-key",
                "0xplayer",
            )

    def test_gzctf_flag_overrides_local_fallback_during_import(self):
        with patch.dict(
            os.environ,
            {
                "FLAG": "HOLOGY9{local_fallback}",
                "GZCTF_FLAG": "HOLOGY9{team_specific}",
            },
        ):
            load_challenge_module()
            self.assertEqual(os.environ["FLAG"], "HOLOGY9{team_specific}")


if __name__ == "__main__":
    unittest.main()
