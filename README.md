# Curb

Curb is a daily record of what a dollar of USDT costs on peer-to-peer markets in Nigeria, Ghana and Kenya, against the reference rate. Each day's numbers are hashed and written to Base, so a published figure cannot be quietly revised later.

Runs entirely on free infrastructure. Total running cost is a few cents a year in gas.

---

## What is in here

```
scripts/fetch_rates.py      Pulls P2P and reference rates, computes the premium
scripts/attest.py           Hashes the day's record, writes it to Base
index.html                  The public page, no build step, no dependencies
data/history.json           Append-only record, one entry per day
data/latest.json            Most recent entry
.github/workflows/daily.yml The daily job
```

The `data/` files currently hold 45 days of **placeholder data** so you can see the page working before the first real run. Delete both files before you go live (step 5).

---

## Prerequisites

| What | Cost | Notes |
| --- | --- | --- |
| GitHub account | Free | Public repo, so Actions minutes are free |
| Python 3.10+ locally | Free | Only needed to test before deploying |
| A wallet with a little ETH on Base | About $5 | Optional. Without it everything still runs, minus the on-chain proof |
| Domain | About $12/year | Optional. GitHub Pages gives you a free URL |

Use a **fresh wallet** for this, holding a few dollars only. Its private key goes into GitHub Secrets, and the wallet does nothing except send zero-value transactions to itself.

---

## Setup, step by step

### 1. Create the repository

On github.com, create a new **public** repository called `curb`. Public matters: private repos have limited free Actions minutes, and the data is meant to be public anyway.

Then, on your machine:

```bash
git clone https://github.com/<your-username>/curb.git
cd curb
```

Copy the contents of this folder into it.

### 2. Test the fetch locally

```bash
pip install -r requirements.txt
python scripts/fetch_rates.py
```

You should see a line per currency, something like `NGN: p2p 1,751.00 vs ref 1,621.94 = +7.96%`.

If Binance P2P returns nothing, the script says so and records `null` for that market rather than inventing a number. If every market fails, it refuses to write at all. That is deliberate: a gap in the data is recoverable, a wrong number that gets published is not.

### 3. Test the page locally

```bash
python -m http.server 8000
```

Open `http://localhost:8000`. You should see the chart, the three markets, and the note about measurement.

### 4. Set up the Base wallet

Skip this if you want to run without the on-chain proof; everything else works.

1. Create a new wallet in MetaMask or any wallet, used only for this.
2. Add the Base network, chain ID 8453.
3. Send about $5 of ETH to it on Base. Buy on any exchange that supports Base withdrawals, or bridge from Ethereum at bridge.base.org.
4. Export the private key.

In your repository, go to Settings, then Secrets and variables, then Actions, then New repository secret:

- Name `ATTEST_PRIVATE_KEY`, value the private key, with or without the `0x`.
- Optionally `BASE_RPC_URL` if you prefer your own RPC endpoint over the public one.

Test it:

```bash
export ATTEST_PRIVATE_KEY=0x...
python scripts/attest.py
```

It prints the transaction link on basescan. Each write costs a fraction of a cent, so $5 covers many years.

### 4b. How to verify a published number

Anyone can check that a figure was not edited after publication:

1. Take the day's entry from `history.json`.
2. Rebuild the canonical payload: date, asset, and each market's `p2p`, `reference` and `premium_pct`, sorted by currency, as compact JSON.
3. SHA-256 it.
4. Compare against the calldata in that day's transaction on basescan.

`scripts/attest.py` contains the exact canonical form, in `canonical_payload`.

### 5. Clear the placeholder data

```bash
rm data/history.json data/latest.json
python scripts/fetch_rates.py
python scripts/attest.py
```

That gives you day one of real data.

### 6. Push and enable the daily job

```bash
git add .
git commit -m "Curb"
git push
```

In the repository, open the Actions tab and enable workflows if prompted. The job runs at 06:05 UTC daily. Use "Run workflow" on the Daily premium snapshot job to trigger it by hand the first time.

### 7. Publish the page

Settings, then Pages. Under Source choose "Deploy from a branch", branch `main`, folder `/ (root)`. Save.

Your page appears at `https://<your-username>.github.io/curb/` within a minute or two.

For a custom domain, add a `CNAME` file containing your domain and point a CNAME record at `<your-username>.github.io`.

---

## Maintenance, honestly

Expect two kinds of breakage.

**Binance changes its P2P endpoint.** The script handles this gracefully, recording `null` and carrying on, but the data stops until you fix the payload shape. Check the page once a week; a flat line or a gap means the fetch is failing.

**The reference rate source changes.** `open.er-api.com` is free and has no key, which also means no support. If it goes away, swap `REFERENCE_FX` for another source and update the wording on the page, since the page states plainly where the number comes from.

Budget about ten minutes a month. If it starts needing more, it is not worth keeping.

---

## Things worth adding later

- XOF and XAF, once you confirm there is enough P2P depth to produce a meaningful median.
- A weekly summary line you can paste straight into a post.
- A second asset, USDC, to show where the two diverge.
- A simple JSON endpoint so other people can pull the series, which is what turns this from a chart into a source other people cite.

Live URL: https://ooracle100.github.io/curb/
