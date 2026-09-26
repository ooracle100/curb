# Curb: patch instructions for the next agent

You are continuing work another agent started. Read `CHANGELOG.md` and `PLAN.md` first for context. This file supersedes `AGENT_BRIEF.md` where they conflict.

The previous agent's finding was correct: Binance removed NGN from P2P in February 2024, and Bybit is live across all three markets. The patch in this folder applies that change plus three others. Apply it, run the tests below, report the results, and stop at the two questions at the end without answering them yourself.

Work through the steps in order. After each one, paste the actual terminal output. Do not summarise output as "worked" or "successful": paste what the command printed.

---

## Step 0. Restructure, if not already done

The scripts assume they live in `scripts/`, because they compute `ROOT` as the parent of their own parent directory. The workflow assumes `.github/workflows/`. Move files so the tree is:

```
curb/
  index.html
  requirements.txt
  README.md
  AGENT_BRIEF.md
  PLAN.md
  CHANGELOG.md
  PATCH_INSTRUCTIONS.md
  scripts/
    fetch_rates.py
    attest.py
    verify.py
    new_wallet.py
  .github/
    workflows/
      daily.yml
      probe.yml
  data/
```

**Expected result:** `ls scripts/` shows four files. `ls .github/workflows/` shows two.

---

## Step 1. Apply the patch

Copy these four files from the patch folder over the project, replacing what is there:

| File | Destination | What changed |
| --- | --- | --- |
| `scripts/fetch_rates.py` | `scripts/fetch_rates.py` | Bybit is now the primary venue, Binance a fallback. Each market records which venue priced it |
| `scripts/attest.py` | `scripts/attest.py` | The hashed payload now includes the venue and a format version |
| `scripts/verify.py` | `scripts/verify.py` | New file. Rebuilds the hash and compares against the chain |
| `index.html` | `index.html` | Shows the venue per market instead of naming Binance in the methodology note |
| `.github/workflows/probe.yml` | `.github/workflows/probe.yml` | New file. Tests endpoint reachability from GitHub runners |

Then delete any existing `data/history.json` and `data/latest.json`. They contain placeholder data in the old format, without the `source` field.

**Expected result:** `git status` (or a directory listing) showing five files changed or added, and `data/` empty.

---

## Step 2. Local fetch test

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch_rates.py
```

**Expected result:** three lines, one per currency, in this shape:

```
  NGN: bybit 1,366.45 vs ref 1,328.96 = +2.82% (380 ads)
  GHS: bybit 12.02 vs ref 11.57 = +3.89% (64 ads)
  KES: bybit 128.60 vs ref 129.51 = -0.70% (58 ads)
wrote 2026-09-27 (1 days on file)
```

Numbers will differ. What must be true: every line names a venue, shows an advert count of 3 or more, and the final line confirms one day on file. A negative premium is a valid result, not a bug.

If a market falls back to Binance, that is fine and the line will say `binance`. If a market returns nothing, the line goes to stderr saying so, and `source` is recorded as null for that market.

---

## Step 3. Confirm the page renders

```bash
python -m http.server 8000
```

Open `http://localhost:8000` and check:

- The chart draws. With one day of data it will say there are not enough readings yet, which is correct.
- Each market tile shows the price pair followed by the venue, for example `1,366.45 vs 1,328.96 · bybit`.
- No console errors other than Google Fonts if you are offline.
- The layout holds at 375px wide.

**Expected result:** a screenshot of the page, plus confirmation of the four points above.

---

## Step 4. Push the probe workflow and run it in CI

This is the most important test in this document, and it must happen before anything depends on the daily job.

Bybit's `api2.bybit.com/fiat/otc/item/online` is the endpoint their web frontend calls, not a documented public API. It answers from a laptop in Lagos. It may behave differently from GitHub's datacenter IP ranges, which exchanges commonly rate-limit or geo-filter.

Push the repository (Step 6 if it does not exist yet), then in the Actions tab run **Endpoint reachability check** manually.

**Expected result:** the run log, pasted in full. It ends with either:

```
Usable from CI: bybit:NGN, bybit:GHS, bybit:KES
```

or a failure line saying no venue returned usable depth.

**If it fails from CI but works locally, stop and report it.** Do not switch data sources on your own. That is a decision for the operator, and the options are different: a proxy, a different venue, or running the job somewhere other than GitHub.

---

## Step 5. Wallet

```bash
python scripts/new_wallet.py
```

Show the operator **the address only**. Tell them to copy the private key from their own terminal into their password manager. Never paste the private key into chat, logs, a file, or a commit.

Then stop. The operator must send about $5 of ETH to that address on Base, chain ID 8453. You cannot do this for them.

When they confirm, verify the balance:

```bash
python -c "
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
print(w3.from_wei(w3.eth.get_balance('<ADDRESS>'), 'ether'), 'ETH')"
```

**Expected result:** a non-zero balance printed.

---

## Step 6. Attest, then verify independently

```bash
export ATTEST_PRIVATE_KEY=<key, from the operator's own shell>
python scripts/attest.py
python scripts/verify.py
```

**Expected result from `attest.py`:**

```
snapshot sha256: ef78b784...
wallet 0x... holds 0.00200000 ETH
attested in block 12345678: https://basescan.org/tx/0x...
```

**Expected result from `verify.py`:**

```
2026-09-27  OK   local ef78b784ef9eae1b... chain ef78b784ef9eae1b...

1/1 days verified
```

`verify.py` reads the calldata back off Base and rebuilds the hash from the published JSON. If it prints FAIL, the attestation is decoration and the project must not go live until it passes. Report the failure rather than working around it.

---

## Step 7. GitHub

Ask the operator to create a **public** repository named `curb`, or to authorise `gh` so you can create it. Public matters: Actions minutes are free on public repositories.

Push, then add the repository secret `ATTEST_PRIVATE_KEY` under Settings, Secrets and variables, Actions. If you cannot set secrets, give the operator the exact path and wait.

**Expected result:** the repository URL, and confirmation the secret exists (its presence is visible in the UI; its value is not).

---

## Step 8. Daily job

Enable Actions. Run **Daily premium snapshot** manually.

**Expected result:** a completed run whose log shows the fetch lines, the attestation transaction link, and a commit of `data/`. Then confirm `data/history.json` in the repository has gained a record.

If the run fails, fix and rerun until a full run passes end to end. Report each fix.

---

## Step 9. Publish

Deploy with GitHub Pages: Settings, Pages, source "Deploy from a branch", branch `main`, folder `/ (root)`.

**Expected result:** the live URL loads with real data, and `<url>/data/history.json` returns JSON in the browser.

---

## Step 10. Record what you did

Append to `CHANGELOG.md`: what you changed, the CI probe result, the first real record date, the live URL, and anything that surprised you. Append the live URL to `README.md`.

---

## Two questions for the operator. Do not answer these yourself.

**Question 1: is the reference rate the right one?**

Run this and report the output:

```bash
python -c "
import requests
r = requests.get('https://open.er-api.com/v6/latest/USD', timeout=20).json()
print('as of', r.get('time_last_update_utc'))
for f in ['NGN','GHS','KES']: print(f, r['rates'][f])"
```

Then look up the Central Bank of Nigeria's published rate for the same day at cbn.gov.ng and report both figures side by side.

Why this matters: if `open.er-api.com` is already tracking the parallel market rather than the official window, the premium shown is close to zero by construction and the page's central claim is weak. The operator decides whether to switch to a central bank rate or to state plainly on the page which rate is used. Do not switch sources on your own.

**Question 2: is the right side of the book being read?**

`fetch_bybit` uses `"side": "1"`. Open Bybit P2P in a browser for NGN and check whether the prices returned by the API match the adverts shown under the tab where merchants are **selling** USDT, which is what a buyer of dollars pays.

Report which tab the numbers match. If they match the buy side instead, say so and stop. Reading the wrong side inverts the premium, and nothing downstream would catch it.

---

## Rules that apply throughout

- Never invent a number to fill a gap. Null is a valid record.
- Never print, log or commit the private key.
- Do not change `canonical_payload` in `attest.py`. It defines what verification means, and altering it invalidates every prior day's proof. If you believe it needs changing, stop and say why.
- If a step fails twice, stop and explain rather than working around it.
- Paste real terminal output, not descriptions of it.
