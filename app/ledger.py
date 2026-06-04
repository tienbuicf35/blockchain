from __future__ import annotations

import csv
import hashlib
import hmac
import io
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from eth_account import Account
    from eth_account.messages import encode_defunct
    from web3 import Web3
except Exception:  # pragma: no cover - optional dependency for local-only mode
    Account = None
    encode_defunct = None
    Web3 = None


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
OFFCHAIN_PATH = DATA_DIR / "offchain" / "prediction_payloads.json"
ONCHAIN_PATH = DATA_DIR / "onchain" / "anchor_chain.json"
LEDGER_PATH = ONCHAIN_PATH
DEFAULT_LEDGER_SECRET = "dev-only-change-me"
DEFAULT_LEDGER_BACKEND = "local"

PREDICTION_LEDGER_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "timestamp", "type": "string"},
            {"internalType": "string", "name": "source", "type": "string"},
            {"internalType": "bytes32", "name": "offchainRecordId", "type": "bytes32"},
            {"internalType": "bytes32", "name": "payloadHash", "type": "bytes32"},
            {"internalType": "bytes32", "name": "previousHash", "type": "bytes32"},
            {"internalType": "bytes32", "name": "anchorHash", "type": "bytes32"},
            {"internalType": "bytes", "name": "signature", "type": "bytes"},
            {"internalType": "string", "name": "storageMode", "type": "string"},
        ],
        "name": "appendAnchor",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "anchorCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "index", "type": "uint256"}],
        "name": "getAnchor",
        "outputs": [
            {"internalType": "uint256", "name": "index", "type": "uint256"},
            {"internalType": "string", "name": "timestamp", "type": "string"},
            {"internalType": "string", "name": "source", "type": "string"},
            {"internalType": "bytes32", "name": "offchainRecordId", "type": "bytes32"},
            {"internalType": "bytes32", "name": "payloadHash", "type": "bytes32"},
            {"internalType": "bytes32", "name": "previousHash", "type": "bytes32"},
            {"internalType": "bytes32", "name": "anchorHash", "type": "bytes32"},
            {"internalType": "bytes", "name": "signature", "type": "bytes"},
            {"internalType": "address", "name": "writer", "type": "address"},
            {"internalType": "string", "name": "storageMode", "type": "string"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


@dataclass
class OffChainRecord:
    record_id: str
    timestamp: str
    source: str
    image_name: str
    image_sha256: str
    model_dir: str
    top_k: int
    predictions: List[Dict[str, Any]]


@dataclass
class OnChainAnchor:
    index: int
    timestamp: str
    source: str
    offchain_record_id: str
    payload_hash: str
    previous_hash: str
    hash: str
    signature: str
    storage: str
    writer_address: str = ""
    tx_hash: str = ""


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _onchain_path() -> Path:
    return LEDGER_PATH


def _storage_root() -> Path:
    onchain_parent = _onchain_path().parent
    if onchain_parent.name.lower() == "onchain" and onchain_parent.parent != onchain_parent:
        return onchain_parent.parent
    return onchain_parent


def _offchain_path() -> Path:
    return _storage_root() / "offchain" / "prediction_payloads.json"


def _canonical_payload(block_data: Dict[str, Any]) -> str:
    return json.dumps(block_data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _record_hash(record_data: Dict[str, Any]) -> str:
    payload = _canonical_payload(record_data).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _secret_key() -> bytes:
    return os.getenv("LEDGER_SECRET_KEY", DEFAULT_LEDGER_SECRET).encode("utf-8")


def _block_signature(block_data: Dict[str, Any]) -> str:
    payload = _canonical_payload(block_data).encode("utf-8")
    return hmac.new(_secret_key(), payload, hashlib.sha256).hexdigest()


def _load_json_list(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        return []
    return data


def _save_json_list(path: Path, payload: List[Dict[str, Any]]) -> None:
    _ensure_parent_dir(path)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


def _load_offchain_records() -> List[Dict[str, Any]]:
    return _load_json_list(_offchain_path())


def _load_onchain_anchors() -> List[Dict[str, Any]]:
    return _load_json_list(_onchain_path())


def _save_offchain_records(records: List[Dict[str, Any]]) -> None:
    _save_json_list(_offchain_path(), records)


def _save_onchain_anchors(anchors: List[Dict[str, Any]]) -> None:
    _save_json_list(_onchain_path(), anchors)


def _selected_backend() -> str:
    backend = os.getenv("LEDGER_BACKEND", "").strip().lower()
    if backend:
        return backend
    if _has_evm_config():
        return "evm"
    return DEFAULT_LEDGER_BACKEND


def _has_evm_config() -> bool:
    return all(
        os.getenv(name, "").strip()
        for name in ("WEB3_PROVIDER_URI", "LEDGER_CONTRACT_ADDRESS", "LEDGER_PRIVATE_KEY")
    )


def _is_evm_backend() -> bool:
    return _selected_backend() in {"evm", "ethereum", "web3"}


def _is_fabric_backend() -> bool:
    return _selected_backend() in {"fabric", "hyperledger", "hyperledger-fabric"}


def _hex_to_bytes32(value: str) -> bytes:
    text = value[2:] if value.startswith("0x") else value
    return bytes.fromhex(text)


def _bytes32_to_hex(value: Any) -> str:
    if hasattr(value, "hex"):
        text = value.hex()
    else:
        text = str(value)
    return text[2:] if text.startswith("0x") else text


def _normalize_signature(value: Any) -> str:
    if isinstance(value, bytes):
        return value.hex()
    if hasattr(value, "hex"):
        text = value.hex()
        return text[2:] if text.startswith("0x") else text
    text = str(value)
    return text[2:] if text.startswith("0x") else text


def _to_checksum_address(value: str) -> str:
    if Web3 is None:
        return value
    return Web3.to_checksum_address(value)


class EvmLedgerBackend:
    def __init__(self) -> None:
        if Web3 is None or Account is None or encode_defunct is None:
            raise RuntimeError(
                "Blockchain backend requires 'web3' and 'eth-account'. Install dependencies and set WEB3_PROVIDER_URI, LEDGER_CONTRACT_ADDRESS, and LEDGER_PRIVATE_KEY."
            )
        provider_uri = os.getenv("WEB3_PROVIDER_URI", "").strip()
        contract_address = os.getenv("LEDGER_CONTRACT_ADDRESS", "").strip()
        private_key = os.getenv("LEDGER_PRIVATE_KEY", "").strip()
        if not provider_uri or not contract_address or not private_key:
            raise RuntimeError(
                "Missing blockchain config. Set WEB3_PROVIDER_URI, LEDGER_CONTRACT_ADDRESS, and LEDGER_PRIVATE_KEY."
            )
        self.w3 = Web3(Web3.HTTPProvider(provider_uri))
        if not self.w3.is_connected():
            raise RuntimeError(f"Could not connect to blockchain provider: {provider_uri}")
        self.contract_address = _to_checksum_address(contract_address)
        self.private_key = private_key
        self.account = Account.from_key(private_key)
        signer_address = os.getenv("LEDGER_SIGNER_ADDRESS", "").strip()
        self.signer_address = _to_checksum_address(signer_address) if signer_address else self.account.address

    @property
    def contract(self) -> Any:
        return self.w3.eth.contract(address=self.contract_address, abi=PREDICTION_LEDGER_ABI)

    def _send_transaction(self, tx_data: Dict[str, Any]) -> str:
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        base_tx = {
            "from": self.account.address,
            "nonce": nonce,
            "chainId": self.w3.eth.chain_id,
        }
        try:
            base_tx["maxFeePerGas"] = self.w3.eth.max_fee_per_gas
            base_tx["maxPriorityFeePerGas"] = self.w3.eth.max_priority_fee_per_gas
        except Exception:
            base_tx["gasPrice"] = self.w3.eth.gas_price

        tx = dict(tx_data)
        tx.update(base_tx)
        if "gas" not in tx:
            try:
                tx["gas"] = int(self.w3.eth.estimate_gas(tx))
            except Exception:
                tx["gas"] = 500000
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status != 1:
            raise RuntimeError("Blockchain transaction failed")
        return tx_hash.hex()

    def _load_anchors(self) -> List[Dict[str, Any]]:
        count = int(self.contract.functions.anchorCount().call())
        anchors: List[Dict[str, Any]] = []
        for i in range(count):
            raw = self.contract.functions.getAnchor(i).call()
            anchors.append(
                {
                    "index": int(raw[0]),
                    "timestamp": str(raw[1]),
                    "source": str(raw[2]),
                    "offchain_record_id": _bytes32_to_hex(raw[3]),
                    "payload_hash": _bytes32_to_hex(raw[4]),
                    "previous_hash": _bytes32_to_hex(raw[5]),
                    "hash": _bytes32_to_hex(raw[6]),
                    "signature": _normalize_signature(raw[7]),
                    "writer_address": str(raw[8]),
                    "storage": str(raw[9]),
                    "tx_hash": "",
                }
            )
        return anchors

    def append_prediction(
        self,
        *,
        source: str,
        image_name: str,
        image_bytes: bytes,
        model_dir: str,
        top_k: int,
        predictions: List[Dict[str, Any]],
    ) -> OnChainAnchor:
        offchain_records = _load_offchain_records()
        offchain_data = _offchain_payload(
            source=source,
            image_name=image_name,
            image_bytes=image_bytes,
            model_dir=model_dir,
            top_k=top_k,
            predictions=predictions,
        )
        record_id = _sha256_text(_canonical_payload(offchain_data))
        offchain_record = OffChainRecord(record_id=record_id, **offchain_data)
        anchors = self._load_anchors()
        payload_hash = _record_hash(asdict(offchain_record))
        if anchors and _anchor_matches_record(anchors[-1], record_id, payload_hash):
            return OnChainAnchor(**anchors[-1])

        offchain_records.append(asdict(offchain_record))
        _save_offchain_records(offchain_records)

        previous_hash = anchors[-1]["hash"] if anchors else "0" * 64
        anchor_payload = {
            "index": len(anchors),
            "timestamp": offchain_record.timestamp,
            "source": source,
            "offchain_record_id": record_id,
            "payload_hash": payload_hash,
            "previous_hash": previous_hash,
            "storage": "off-chain-json",
        }
        anchor_hash = _record_hash(anchor_payload)
        signature = Account.sign_message(encode_defunct(text=anchor_hash), private_key=self.private_key).signature
        tx_hash = self._send_transaction(
            self.contract.functions.appendAnchor(
                offchain_record.timestamp,
                source,
                _hex_to_bytes32(record_id),
                _hex_to_bytes32(payload_hash),
                _hex_to_bytes32(previous_hash),
                _hex_to_bytes32(anchor_hash),
                signature,
                "off-chain-json",
            ).build_transaction({})
        )
        anchor = OnChainAnchor(
            hash=anchor_hash,
            signature=_normalize_signature(signature),
            writer_address=self.account.address,
            tx_hash=tx_hash,
            **anchor_payload,
        )
        return anchor


class FabricLedgerBackend:
    """Hybrid Fabric adapter.

    The app still keeps the sensitive prediction payload off-chain. The Fabric
    transaction anchors only hashes and audit metadata, which is the safer shape
    for medical screening data.
    """

    def __init__(self) -> None:
        self.peer_command = os.getenv("FABRIC_PEER_COMMAND", "peer").strip() or "peer"
        self.channel_name = os.getenv("FABRIC_CHANNEL_NAME", "").strip()
        self.chaincode_name = os.getenv("FABRIC_CHAINCODE_NAME", "prediction-ledger").strip()
        self.require_commit = os.getenv("FABRIC_REQUIRE_COMMIT", "false").strip().lower() in {"1", "true", "yes"}

    @property
    def configured(self) -> bool:
        return bool(self.channel_name and self.chaincode_name)

    def _submit_anchor(self, anchor: OnChainAnchor) -> str:
        if not self.configured:
            if self.require_commit:
                raise RuntimeError("Missing Fabric config. Set FABRIC_CHANNEL_NAME and FABRIC_CHAINCODE_NAME.")
            return ""

        payload = {
            "function": "RecordPredictionAnchor",
            "Args": [
                str(anchor.index),
                anchor.timestamp,
                anchor.source,
                anchor.offchain_record_id,
                anchor.payload_hash,
                anchor.previous_hash,
                anchor.hash,
                anchor.signature,
                anchor.storage,
            ],
        }
        cmd = [
            self.peer_command,
            "chaincode",
            "invoke",
            "-C",
            self.channel_name,
            "-n",
            self.chaincode_name,
            "-c",
            json.dumps(payload, separators=(",", ":")),
        ]
        try:
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        except FileNotFoundError as exc:
            if self.require_commit:
                raise RuntimeError(f"Fabric peer command not found: {self.peer_command}") from exc
            return ""
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "Fabric chaincode invoke failed").strip()
            if self.require_commit:
                raise RuntimeError(message)
            return ""
        return _sha256_text(result.stdout.strip() or anchor.hash)

    def append_prediction(
        self,
        *,
        source: str,
        image_name: str,
        image_bytes: bytes,
        model_dir: str,
        top_k: int,
        predictions: List[Dict[str, Any]],
    ) -> OnChainAnchor:
        anchor = _append_prediction_local(
            source=source,
            image_name=image_name,
            image_bytes=image_bytes,
            model_dir=model_dir,
            top_k=top_k,
            predictions=predictions,
            storage="fabric-private-data+off-chain-json",
            writer_address=os.getenv("FABRIC_MSP_ID", ""),
        )
        if anchor.tx_hash:
            return anchor
        tx_hash = self._submit_anchor(anchor)
        if not tx_hash:
            return anchor

        anchors = _load_onchain_anchors()
        if anchors and anchors[-1].get("hash") == anchor.hash:
            anchors[-1]["tx_hash"] = tx_hash
            _save_onchain_anchors(anchors)
            return OnChainAnchor(**anchors[-1])
        return anchor


def _image_digest(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()


def _offchain_payload(
    *,
    source: str,
    image_name: str,
    image_bytes: bytes,
    model_dir: str,
    top_k: int,
    predictions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "source": source,
        "image_name": image_name,
        "image_sha256": _image_digest(image_bytes),
        "model_dir": model_dir,
        "top_k": top_k,
        "predictions": predictions,
    }


def _merge_anchor_with_record(
    anchor: Dict[str, Any],
    record_map: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    record = record_map.get(str(anchor.get("offchain_record_id", "")), {})
    merged = {**record, **anchor}
    merged.setdefault("record_id", str(anchor.get("offchain_record_id", "")))
    merged.setdefault("storage", "off-chain-json")
    return merged


def _anchor_matches_record(anchor: Dict[str, Any], record_id: str, payload_hash: str) -> bool:
    return str(anchor.get("offchain_record_id", "")) == record_id and str(anchor.get("payload_hash", "")) == payload_hash


def _already_appended(anchors: List[Dict[str, Any]], record_id: str, payload_hash: str) -> bool:
    if not anchors:
        return False
    return _anchor_matches_record(anchors[-1], record_id, payload_hash)


def append_prediction(
    *,
    source: str,
    image_name: str,
    image_bytes: bytes,
    model_dir: str,
    top_k: int,
    predictions: List[Dict[str, Any]],
) -> OnChainAnchor:
    if _is_evm_backend():
        return EvmLedgerBackend().append_prediction(
            source=source,
            image_name=image_name,
            image_bytes=image_bytes,
            model_dir=model_dir,
            top_k=top_k,
            predictions=predictions,
        )
    if _is_fabric_backend():
        return FabricLedgerBackend().append_prediction(
            source=source,
            image_name=image_name,
            image_bytes=image_bytes,
            model_dir=model_dir,
            top_k=top_k,
            predictions=predictions,
        )

    return _append_prediction_local(
        source=source,
        image_name=image_name,
        image_bytes=image_bytes,
        model_dir=model_dir,
        top_k=top_k,
        predictions=predictions,
    )


def _append_prediction_local(
    *,
    source: str,
    image_name: str,
    image_bytes: bytes,
    model_dir: str,
    top_k: int,
    predictions: List[Dict[str, Any]],
    storage: str = "off-chain-json",
    writer_address: str = "",
    tx_hash: str = "",
) -> OnChainAnchor:
    offchain_records = _load_offchain_records()
    anchors = _load_onchain_anchors()

    offchain_data = _offchain_payload(
        source=source,
        image_name=image_name,
        image_bytes=image_bytes,
        model_dir=model_dir,
        top_k=top_k,
        predictions=predictions,
    )
    record_id = _sha256_text(_canonical_payload(offchain_data))
    offchain_record = OffChainRecord(record_id=record_id, **offchain_data)
    payload_hash = _record_hash(asdict(offchain_record))
    if _already_appended(anchors, record_id, payload_hash):
        last_anchor = anchors[-1]
        return OnChainAnchor(**last_anchor)
    offchain_records.append(asdict(offchain_record))
    _save_offchain_records(offchain_records)

    previous_hash = anchors[-1]["hash"] if anchors else "0" * 64
    anchor_payload = {
        "index": len(anchors),
        "timestamp": offchain_record.timestamp,
        "source": source,
        "offchain_record_id": record_id,
        "payload_hash": payload_hash,
        "previous_hash": previous_hash,
        "storage": storage,
    }
    anchor_hash = _record_hash(anchor_payload)
    signature = _block_signature({**anchor_payload, "hash": anchor_hash})
    anchor = OnChainAnchor(
        hash=anchor_hash,
        signature=signature,
        writer_address=writer_address,
        tx_hash=tx_hash,
        **anchor_payload,
    )
    anchors.append(asdict(anchor))
    _save_onchain_anchors(anchors)
    return anchor


def get_chain(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    if _is_evm_backend():
        anchors = EvmLedgerBackend()._load_anchors()
        records = _load_offchain_records()
        record_map = {str(item.get("record_id", "")): item for item in records}
        merged_chain = [_merge_anchor_with_record(anchor, record_map) for anchor in anchors]
        if limit is None or limit >= len(merged_chain):
            return merged_chain
        return merged_chain[-limit:]

    anchors = _load_onchain_anchors()
    records = _load_offchain_records()
    record_map = {str(item.get("record_id", "")): item for item in records}
    merged_chain = [_merge_anchor_with_record(anchor, record_map) for anchor in anchors]
    if limit is None or limit >= len(merged_chain):
        return merged_chain
    return merged_chain[-limit:]


def get_chain_summary() -> Dict[str, Any]:
    if _is_evm_backend():
        anchors = EvmLedgerBackend()._load_anchors()
        records = _load_offchain_records()
        validation = validate_chain()
        head_hash = anchors[-1]["hash"] if anchors else ""
        tail_hash = anchors[0]["hash"] if anchors else ""
        return {
            "backend": "hybrid-evm",
            "onchain_length": len(anchors),
            "offchain_length": len(records),
            "length": len(anchors),
            "valid": bool(validation.get("valid", False)),
            "broken_index": int(validation.get("broken_index", -1)),
            "reason": str(validation.get("reason", "")),
            "head_hash": head_hash,
            "tail_hash": tail_hash,
            "last_source": anchors[-1]["source"] if anchors else "",
            "last_timestamp": anchors[-1]["timestamp"] if anchors else "",
        }

    anchors = _load_onchain_anchors()
    records = _load_offchain_records()
    validation = validate_chain()
    head_hash = anchors[-1]["hash"] if anchors else ""
    tail_hash = anchors[0]["hash"] if anchors else ""
    return {
        "backend": "hybrid-fabric" if _is_fabric_backend() else "hybrid-local",
        "onchain_length": len(anchors),
        "offchain_length": len(records),
        "length": len(anchors),
        "valid": bool(validation.get("valid", False)),
        "broken_index": int(validation.get("broken_index", -1)),
        "reason": str(validation.get("reason", "")),
        "head_hash": head_hash,
        "tail_hash": tail_hash,
        "last_source": anchors[-1]["source"] if anchors else "",
        "last_timestamp": anchors[-1]["timestamp"] if anchors else "",
    }


def _validate_offchain_record(record: Dict[str, Any]) -> Tuple[bool, str, str]:
    payload = {k: record[k] for k in record if k != "record_id"}
    expected_record_id = _sha256_text(_canonical_payload(payload))
    if record.get("record_id") != expected_record_id:
        return False, "offchain-id-mismatch", expected_record_id
    return True, "", expected_record_id


def _validate_evm_chain() -> Dict[str, Any]:
    backend = EvmLedgerBackend()
    anchors = backend._load_anchors()
    records = _load_offchain_records()
    record_map = {str(item.get("record_id", "")): item for item in records}

    for i, anchor in enumerate(anchors):
        expected_prev = "0" * 64 if i == 0 else anchors[i - 1]["hash"]
        anchor_payload = {k: anchor[k] for k in anchor if k not in ("hash", "signature", "writer_address", "tx_hash")}
        expected_hash = _record_hash(anchor_payload)
        signature = anchor.get("signature", "")

        if anchor.get("previous_hash") != expected_prev:
            return {
                "valid": False,
                "broken_index": i,
                "length": len(anchors),
                "offchain_length": len(records),
                "reason": "broken-link",
            }
        if anchor.get("hash") != expected_hash:
            return {
                "valid": False,
                "broken_index": i,
                "length": len(anchors),
                "offchain_length": len(records),
                "reason": "hash-mismatch",
            }
        if not signature:
            return {
                "valid": False,
                "broken_index": i,
                "length": len(anchors),
                "offchain_length": len(records),
                "reason": "missing-signature",
            }
        if Account is not None and encode_defunct is not None:
            recovered = Account.recover_message(
                encode_defunct(text=expected_hash),
                signature=bytes.fromhex(str(signature)),
            )
            if recovered.lower() != str(anchor.get("writer_address", "")).lower():
                return {
                    "valid": False,
                    "broken_index": i,
                    "length": len(anchors),
                    "offchain_length": len(records),
                    "reason": "signature-mismatch",
                }

        record_id = str(anchor.get("offchain_record_id", ""))
        record = record_map.get(record_id)
        if record is None:
            return {
                "valid": False,
                "broken_index": i,
                "length": len(anchors),
                "offchain_length": len(records),
                "reason": "missing-offchain-record",
            }

        record_valid, reason, _ = _validate_offchain_record(record)
        if not record_valid:
            return {
                "valid": False,
                "broken_index": i,
                "length": len(anchors),
                "offchain_length": len(records),
                "reason": reason,
            }

        payload_hash = _record_hash(record)
        if anchor.get("payload_hash") != payload_hash:
            return {
                "valid": False,
                "broken_index": i,
                "length": len(anchors),
                "offchain_length": len(records),
                "reason": "payload-hash-mismatch",
            }

    return {"valid": True, "length": len(anchors), "offchain_length": len(records)}


def validate_chain() -> Dict[str, Any]:
    if _is_evm_backend():
        return _validate_evm_chain()

    anchors = _load_onchain_anchors()
    records = _load_offchain_records()
    record_map = {str(item.get("record_id", "")): item for item in records}

    for i, anchor in enumerate(anchors):
        expected_prev = "0" * 64 if i == 0 else anchors[i - 1]["hash"]
        anchor_payload = {k: anchor[k] for k in anchor if k not in ("hash", "signature", "writer_address", "tx_hash")}
        expected_hash = _record_hash(anchor_payload)
        expected_signature = _block_signature({**anchor_payload, "hash": expected_hash})

        if anchor.get("previous_hash") != expected_prev:
            return {
                "valid": False,
                "broken_index": i,
                "length": len(anchors),
                "offchain_length": len(records),
                "reason": "broken-link",
            }
        if anchor.get("hash") != expected_hash:
            return {
                "valid": False,
                "broken_index": i,
                "length": len(anchors),
                "offchain_length": len(records),
                "reason": "hash-mismatch",
            }
        if anchor.get("signature") != expected_signature:
            return {
                "valid": False,
                "broken_index": i,
                "length": len(anchors),
                "offchain_length": len(records),
                "reason": "signature-mismatch",
            }

        record_id = str(anchor.get("offchain_record_id", ""))
        record = record_map.get(record_id)
        if record is None:
            return {
                "valid": False,
                "broken_index": i,
                "length": len(anchors),
                "offchain_length": len(records),
                "reason": "missing-offchain-record",
            }

        record_valid, reason, _ = _validate_offchain_record(record)
        if not record_valid:
            return {
                "valid": False,
                "broken_index": i,
                "length": len(anchors),
                "offchain_length": len(records),
                "reason": reason,
            }

        payload_hash = _record_hash(record)
        if anchor.get("payload_hash") != payload_hash:
            return {
                "valid": False,
                "broken_index": i,
                "length": len(anchors),
                "offchain_length": len(records),
                "reason": "payload-hash-mismatch",
            }

    return {"valid": True, "length": len(anchors), "offchain_length": len(records)}


def export_chain_json(limit: Optional[int] = None) -> str:
    return json.dumps(get_chain(limit=limit), ensure_ascii=False, indent=2)


def export_chain_csv(limit: Optional[int] = None) -> str:
    chain = get_chain(limit=limit)
    output = io.StringIO()
    fieldnames = [
        "index",
        "timestamp",
        "source",
        "image_name",
        "image_sha256",
        "model_dir",
        "top_k",
        "predictions",
        "record_id",
        "offchain_record_id",
        "payload_hash",
        "storage",
        "previous_hash",
        "hash",
        "signature",
        "writer_address",
        "tx_hash",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for block in chain:
        row = dict(block)
        row["predictions"] = json.dumps(row.get("predictions", []), ensure_ascii=False)
        writer.writerow(row)
    return output.getvalue()
