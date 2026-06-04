import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from app import ledger


class LedgerTest(unittest.TestCase):
    def test_append_validate_and_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original_path = ledger.LEDGER_PATH
            try:
                ledger.LEDGER_PATH = Path(tmp) / "prediction_chain.json"
                block = ledger.append_prediction(
                    source="test",
                    image_name="a.jpg",
                    image_bytes=b"abc",
                    model_dir="local-model",
                    top_k=3,
                    predictions=[{"code": "MEL", "label": "Melanoma", "score": 0.9}],
                )
                self.assertEqual(block.index, 0)
                self.assertTrue(block.offchain_record_id)
                self.assertTrue(block.signature)

                validation = ledger.validate_chain()
                self.assertTrue(validation["valid"])
                self.assertEqual(validation["length"], 1)
                self.assertEqual(validation["offchain_length"], 1)

                summary = ledger.get_chain_summary()
                self.assertTrue(summary["valid"])
                self.assertEqual(summary["length"], 1)
                self.assertEqual(summary["onchain_length"], 1)
                self.assertEqual(summary["offchain_length"], 1)
                self.assertTrue(summary["head_hash"])

                json_export = ledger.export_chain_json()
                csv_export = ledger.export_chain_csv()
                self.assertIn('"signature"', json_export)
                self.assertIn("signature", csv_export)
                self.assertIn("offchain_record_id", json_export)
            finally:
                ledger.LEDGER_PATH = original_path

    def test_fabric_backend_anchors_prediction_locally_when_peer_is_not_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original_path = ledger.LEDGER_PATH
            try:
                ledger.LEDGER_PATH = Path(tmp) / "anchor_chain.json"
                with patch.dict("os.environ", {"LEDGER_BACKEND": "fabric", "FABRIC_MSP_ID": "Org1MSP"}, clear=False):
                    block = ledger.append_prediction(
                        source="fabric-test",
                        image_name="case.jpg",
                        image_bytes=b"fabric-image",
                        model_dir="local-model",
                        top_k=2,
                        predictions=[{"code": "BCC", "label": "Basal Cell Carcinoma", "score": 0.8}],
                    )
                    self.assertEqual(block.index, 0)
                    self.assertEqual(block.storage, "fabric-private-data+off-chain-json")
                    self.assertEqual(block.writer_address, "Org1MSP")

                    summary = ledger.get_chain_summary()
                    self.assertEqual(summary["backend"], "hybrid-fabric")
                    self.assertTrue(summary["valid"])

                    exported = ledger.export_chain_json()
                    self.assertIn("fabric-private-data+off-chain-json", exported)
            finally:
                ledger.LEDGER_PATH = original_path


if __name__ == "__main__":
    unittest.main()
