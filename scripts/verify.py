#!/usr/bin/env python3
"""Verify that published numbers match what was written to Base.

Rebuilds the SHA-256 from data/history.json, pulls the transaction calldata
from Base, and compares. This is the check that makes the attestation mean
something; without it the transaction is decoration.

Usage:
    python scripts/verify.py              # verify every attested day
    python scripts/verify.py 2026-09-27   # verify one day

Exits 0 when every checked day matches, 1 otherwise.
"""

import json
import os
import sys
from pathlib import Path

from attest import canonical_payload  # same canonical form, by construction

import hashlib
import requests

ROOT = Path(__file__).resolve().parent.parent
HISTORY = ROOT / "data" / "history.json"
RPC_URL = os.environ.get("BASE_RPC_URL", "https://mainnet.base.org")


def calldata_for(tx_hash: str) -> bytes:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_getTransactionByHash",
        "params": [tx_hash],
    }
    r = requests.post(RPC_URL, json=body, timeout=20)
    r.raise_for_status()
    result = r.json().get("result")
    if not result:
        raise RuntimeError(f"transaction {tx_hash} not found on chain")
    return bytes.fromhex(result["input"][2:])


def check(entry) -> bool:
    date = entry["date"]
    att = entry.get("attestation")
    if not att or not att.get("tx"):
        print(f"{date}  no attestation recorded, skipped")
        return True

    local = hashlib.sha256(canonical_payload(entry)).hexdigest()

    try:
        data = calldata_for(att["tx"])
    except Exception as exc:
        print(f"{date}  FAIL could not read chain ({exc})")
        return False

    # calldata is b"CURB:<date>:" + 32 raw bytes of digest
    onchain = data[-32:].hex()
    prefix = data[: -32].decode(errors="replace")

    ok = (local == onchain) and (date in prefix)
    print(f"{date}  {'OK  ' if ok else 'FAIL'} local {local[:16]}... chain {onchain[:16]}...")
    if not ok:
        print(f"         recorded hash {att['sha256'][:16]}...  prefix {prefix!r}")
    return ok


def main():
    history = json.loads(HISTORY.read_text())
    if len(sys.argv) > 1:
        history = [h for h in history if h["date"] == sys.argv[1]]
        if not history:
            print(f"no record for {sys.argv[1]}")
            sys.exit(1)

    results = [check(entry) for entry in history]
    passed, total = sum(results), len(results)
    print(f"\n{passed}/{total} days verified")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
