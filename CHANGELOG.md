# Curb: Changelog

All changes made by agents, with rationale, so any future agent can pick up context immediately.

---

## 2026-09-26 — Initial assessment (no code changes)

**Agent:** Antigravity (Conversation 62b56632)

### What was done

1. Read all project files: `AGENT_BRIEF.md`, `README.md`, `fetch_rates.py`, `attest.py`, `new_wallet.py`, `daily.yml`, `index.html`, `requirements.txt`
2. Tested Binance P2P endpoint live against NGN, GHS, KES — all returned zero adverts
3. Tested reference FX API (`open.er-api.com`) — working, returns valid rates
4. Confirmed `p2p.binance.com` DNS is blocked locally but resolves via Google DNS
5. Researched current state of Binance P2P for Nigeria — **NGN removed from Binance P2P in Feb 2024**
6. Identified Bybit as the leading replacement for Nigerian P2P
7. Identified structural issue: all files flat in root, but scripts expect `scripts/` subfolder

### What was NOT done

- No code was modified
- No files were moved
- No environment was created
- Awaiting operator decisions on data source and deployment target

### Decisions pending

1. Which P2P data source to use for NGN (Bybit recommended)
2. Whether to update page methodology text to reflect new source
3. GitHub Pages vs Vercel for deployment

### Key finding

The project's primary data source (Binance P2P for NGN) has been dead since Feb 2024. The code is well-written and the concept is valuable, but the data pipeline needs a new source before anything can go live. See `PLAN.md` for full analysis and options.
