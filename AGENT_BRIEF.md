# Curb: brief for the coding agent

Paste this whole file to Antigravity as the task. It describes what to do, what to verify, and the four points where you must stop and ask the operator.

---

## The task

Take Curb from files on disk to a live, self-updating public page.

The project records the daily gap between the peer-to-peer price of USDT and the reference FX rate in Nigeria, Ghana and Kenya, hashes each day's numbers, and writes that hash to Base so published figures can be verified later.

Everything needed is in this folder: fetch script, attestation script, wallet generator, page, daily workflow, README.

## Rules

- Do not invent data. If a source returns nothing, record null. Never fabricate a rate to make a chart look complete.
- Do not print, log or commit the private key. It belongs in GitHub Secrets and a password manager, nowhere else.
- Do not change the canonical payload in `scripts/attest.py` without saying so. It is what makes published numbers verifiable, and changing it silently breaks every prior day's proof.
- Report what you did after each step, with the command output that proves it worked.
- If a step fails twice, stop and explain rather than working around it.

## Steps

### 1. Environment

Create a virtualenv, install `requirements.txt`, confirm Python 3.10 or later. Report versions.

### 2. Live fetch test

Run `python scripts/fetch_rates.py` against real endpoints.

This is the step most likely to fail, because Binance's P2P endpoint changes shape without notice. If no adverts come back:

- Check the response body before assuming the URL is wrong.
- If the payload shape changed, fix `fetch_p2p_price` to match, and say exactly what you changed.
- If Binance blocks the request outright, report it. Do not substitute a different exchange without asking, since the README describes this source specifically.

Success looks like a premium figure per currency. Report all three.

### 3. Page test

Serve the folder, open the page, confirm: the chart renders, all three markets switch correctly, no console errors, the layout holds at 375px wide. Screenshot it.

### 4. STOP: wallet

Run `python scripts/new_wallet.py`. Show the operator the address only. Tell them to copy the private key into their password manager from their own terminal.

Then wait. The operator must fund that address with about $5 of ETH on Base, chain ID 8453. You cannot do this for them.

When they confirm funding, verify the balance on-chain before continuing.

### 5. Attestation test

With `ATTEST_PRIVATE_KEY` set in the local environment only, run `python scripts/attest.py`. Confirm the transaction lands and report the basescan link.

Then verify the proof independently: rebuild the SHA-256 from `data/latest.json` using the canonical form in the script, decode the calldata from the transaction, and confirm they match. Report both hashes. If they do not match, the attestation is decoration and must be fixed before going live.

### 6. Clear placeholder data

`data/history.json` and `data/latest.json` currently hold 45 days of fabricated data for layout testing. Delete both, then run the fetch and attest scripts once to create day one of real data. Confirm the files contain exactly one record.

### 7. STOP: GitHub

Ask the operator to create a public repository, or to authorise `gh` so you can create it. Public matters: Actions minutes are free on public repos.

Push the project. Then add the repository secret `ATTEST_PRIVATE_KEY`. If you cannot set secrets yourself, give the operator the exact path in the GitHub UI and wait for confirmation.

### 8. Daily job

Enable Actions. Trigger the Daily premium snapshot workflow by hand. Watch the run to completion and report: did it fetch, did it attest, did it commit the new record. If it fails, fix it and rerun until a full run succeeds.

### 9. Publish

Deploy the page. GitHub Pages from the repository root is the simplest route and the README assumes it. Vercel also works if the operator prefers it, given they already use it. Either way, confirm the live URL loads with real data and that `data/history.json` is reachable from the page.

### 10. Operating notes

Append a short section to the README recording: what the live URL is, anything you changed in the fetch logic and why, and the date of the first real record.

## Acceptance

Do not report the build complete until all five are true:

1. The page is live at a public URL and shows real data.
2. The daily workflow has completed a full successful run end to end.
3. A transaction on Base contains the hash of the current day's record, and you have verified the hash matches.
4. `data/history.json` contains only real records.
5. The private key appears nowhere in the repository, the logs or the chat.

## Where the operator is needed

Four points only. Everything else is yours.

| When | What they do |
| --- | --- |
| Step 4 | Save the private key, fund the address with about $5 of ETH on Base |
| Step 7 | Create the repository or authorise `gh`, and add the secret if you cannot |
| Step 9 | Choose GitHub Pages or Vercel, and connect a domain if they want one |
| Any failure | Decide, when a data source has changed enough that the approach needs rethinking |
