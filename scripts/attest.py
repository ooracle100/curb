#!/usr/bin/env python3
"""Anchor the day's snapshot on Base.

Hashes data/latest.json, sends the hash as calldata in a zero-value transaction
from your wallet to itself, and records the transaction hash back into the day's
record. Anyone can then verify the published numbers were not edited later.

No contract to deploy. Costs a fraction of a cent per day on Base.
Skips quietly when no private key is configured, so the tracker still runs.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
HISTORY = DATA / "history.json"
LATEST = DATA / "latest.json"

RPC_URL = os.environ.get("BASE_RPC_URL", "https://mainnet.base.org")
PRIVATE_KEY = os.environ.get("ATTEST_PRIVATE_KEY", "").strip()
EXPLORER = "https://basescan.org/tx/"

# Version of the canonical payload format. Bump ONLY if the hashed fields
# change, and say so in the README: every prior day's proof is built against
# the format that was current when it was written.
PAYLOAD_VERSION = 1


def canonical_payload(record: dict) -> bytes:
    """The exact bytes that get hashed.

    Includes the venue each price came from, so a change of source is inside
    the proof rather than an undocumented shift in the series. Excludes
    fetched_at, which varies by run and would make the hash irreproducible.
    """
    payload = {
        "v": PAYLOAD_VERSION,
        "date": record["date"],
        "asset": record["asset"],
        "markets": {
            fiat: {
                "p2p": m["p2p"],
                "reference": m["reference"],
                "premium_pct": m["premium_pct"],
                "source": m.get("source"),
            }
            for fiat, m in sorted(record["markets"].items())
        },
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def main():
    record = json.loads(LATEST.read_text())
    digest = hashlib.sha256(canonical_payload(record)).hexdigest()
    print(f"snapshot sha256: {digest}")

    if not PRIVATE_KEY:
        print("ATTEST_PRIVATE_KEY not set, skipping the on-chain write")
        return

    from web3 import Web3

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print(f"cannot reach {RPC_URL}", file=sys.stderr)
        sys.exit(1)

    account = w3.eth.account.from_key(PRIVATE_KEY)
    balance = w3.eth.get_balance(account.address)
    print(f"wallet {account.address} holds {w3.from_wei(balance, 'ether'):.6f} ETH")

    if balance == 0:
        print("wallet is empty, skipping the on-chain write", file=sys.stderr)
        return

    # Tag the calldata so it is identifiable on-chain, then the digest.
    calldata = b"CURB:" + record["date"].encode() + b":" + bytes.fromhex(digest)

    tx = {
        "from": account.address,
        "to": account.address,
        "value": 0,
        "data": "0x" + calldata.hex(),
        "nonce": w3.eth.get_transaction_count(account.address),
        "chainId": w3.eth.chain_id,
    }
    tx["gas"] = int(w3.eth.estimate_gas(tx) * 1.2)
    tx["maxFeePerGas"] = w3.eth.gas_price * 2
    tx["maxPriorityFeePerGas"] = w3.to_wei(0.001, "gwei")

    signed = account.sign_transaction(tx)
    raw = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction")
    tx_hash = w3.eth.send_raw_transaction(raw)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    tx_hex = receipt.transactionHash.hex()
    if not tx_hex.startswith("0x"):
        tx_hex = "0x" + tx_hex
    print(f"attested in block {receipt.blockNumber}: {EXPLORER}{tx_hex}")

    record["attestation"] = {
        "sha256": digest,
        "chain": "base",
        "tx": tx_hex,
        "payload_version": PAYLOAD_VERSION,
    }
    LATEST.write_text(json.dumps(record, indent=2) + "\n")

    history = json.loads(HISTORY.read_text())
    for entry in history:
        if entry.get("date") == record["date"]:
            entry["attestation"] = record["attestation"]
    HISTORY.write_text(json.dumps(history, indent=2) + "\n")


if __name__ == "__main__":
    main()
