#!/usr/bin/env python3
"""Generate a throwaway wallet for on-chain attestation.

Prints the address and private key once. Nothing is saved to disk: copy the
private key into your password manager and into the GitHub secret, then close
the terminal.

This wallet's only job is sending zero-value transactions to itself. Keep about
$5 of ETH on Base in it and nothing else, ever.
"""

from eth_account import Account


def main():
    Account.enable_unaudited_hdwallet_features()
    account, mnemonic = Account.create_with_mnemonic()

    print()
    print("Address      ", account.address)
    print("Private key  ", account.key.hex())
    print("Recovery      ", mnemonic)
    print()
    print("Save the private key now. It is not written to disk and cannot be recovered")
    print("from this script. Fund the address with about $5 of ETH on Base (chain 8453).")
    print()


if __name__ == "__main__":
    main()
