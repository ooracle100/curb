# Curb: Execution Plan

**Created:** 2026-09-26  
**Status:** Awaiting operator approval before execution

---

## 1. Is the data real?

**Yes. All three markets are live and producing real prices right now — from Bybit, not Binance.**

### Live test results (2026-09-26, ~20:53 UTC+1)

| Market | P2P Median | Reference | Premium | Depth |
|--------|-----------|-----------|---------|-------|
| **NGN** | ₦1,366.45 | ₦1,328.96 | **+2.82%** | 380 ads |
| **GHS** | ₵12.02 | ₵11.57 | **+3.89%** | 64 ads |
| **KES** | KSh128.60 | KSh129.51 | **-0.70%** | 58 ads |

These are real prices from real merchants, right now, on Bybit P2P. The Nigerian market alone has 380 active sell adverts — this is a deep, liquid market.

Kenya is interesting: the P2P price is actually *below* the reference rate (-0.70%), meaning USDT is trading at a slight discount. This happens when a country has decent dollar liquidity. That's a data point worth publishing too.

### Why not Binance?

**Binance removed NGN from P2P in February 2024.** It's been gone for over two years. The endpoint still responds (with `"data":[], "total":0`), but there are no adverts to return. GHS and KES may still have some Binance P2P activity, but from your local network the domain doesn't even resolve — likely ISP-level blocking.

### What about other sources?

| Source | Tested? | Result |
|--------|---------|--------|
| **Bybit** (`api2.bybit.com/fiat/otc/item/online`) | ✅ Yes | **Working.** 380 NGN ads, 64 GHS, 58 KES. No auth needed. Free. |
| **Binance** (`p2p.binance.com/bapi/c2c/adv/search`) | ✅ Yes | Dead for NGN. DNS blocked locally. Empty results via resolved IP. |
| **OKX** (`www.okx.com/v3/c2c/tradingOrders/...`) | ✅ Yes | Returned `405 Method Not Allowed` — endpoint has changed or needs different params |
| **Noones** (`api.noones.com`) | ✅ Yes | `resource_not_found` — API requires auth or different endpoint structure |
| **P2P.army** (aggregator) | ✅ Yes | 404 — needs API key signup, free tier has limits, paid starts at $99/mo |

**Bybit is the clear winner.** Public endpoint, no auth needed, deep liquidity in all three markets, structured JSON response. The code change is straightforward.

---

## 2. Why would people care about this?

### The problem

In Nigeria, Ghana, and Kenya, the price you actually pay for dollars is often significantly higher than the "official" or reference rate. This gap — the P2P premium — is one of the most important economic signals in these countries:

- It reflects **capital controls**, forex scarcity, and how much people trust their currency
- It's what **remittance senders** and **importers** actually pay
- It's a proxy for **monetary policy effectiveness** — when it spikes, something is wrong
- It moves before official devaluations happen, making it a **leading indicator**

### The gap in the market

**Nobody publishes this data consistently, daily, with a verifiable audit trail.** You can open Bybit right now and see today's prices. But:

- There's no public archive of what the price was 30 days ago
- Nobody tracks whether published numbers were quietly revised later
- No one computes the premium against the reference rate automatically
- There's no citable URL a journalist can link to

### Who would use it

| Audience | Use case |
|---|---|
| **Journalists** | "The naira premium hit X% this week" — needs a citable, tamper-proof source |
| **Researchers / economists** | Time-series data on parallel market premiums is almost impossible to find |
| **Fintech / remittance operators** | Need to know the real spread for pricing |
| **Policy watchers** | Premium is a leading indicator for FX policy changes |
| **Diaspora** | Want to know the real cost of sending money home |

### What makes Curb different from just checking Bybit yourself

1. **Historical record** — append-only JSON, one entry per day, accumulating over months/years
2. **Tamper-proof** — daily hash on Base means published figures can't be silently revised
3. **Computed metric** — the premium (P2P vs reference) isn't something Bybit shows; Curb calculates it
4. **Citable** — a public URL with clear methodology that can be linked to in articles and papers

The on-chain attestation turns this from "some guy's chart" into a verifiable data source.

---

## 3. What needs to change in the code

### Data source: Binance → Bybit

The only significant code change is in `fetch_rates.py`. The function `fetch_p2p_price` currently calls Binance's endpoint. It needs to call Bybit's instead.

**Bybit endpoint:** `POST https://api2.bybit.com/fiat/otc/item/online`

**Payload:**
```json
{
  "userId": "",
  "tokenId": "USDT",
  "currencyId": "NGN",
  "payment": [],
  "side": "1",
  "size": "10",
  "page": "1",
  "amount": ""
}
```

**Response shape:** `response.result.items[].price` — string, needs `float()` conversion. Same median logic applies.

The change is surgical: ~15 lines in one function. Everything else (attestation, page, workflow) stays the same.

### Page text

The methodology note on `index.html` currently says "the ten deepest sell adverts on Binance P2P". This needs to say "Bybit P2P" instead. One line change.

### Folder structure

All files are currently flat in root. They need to be moved to match the structure the scripts and workflow expect:

```
curb/
  index.html
  requirements.txt
  README.md
  AGENT_BRIEF.md
  PLAN.md
  CHANGELOG.md
  scripts/
    fetch_rates.py    ← moved from root
    attest.py         ← moved from root  
    new_wallet.py     ← moved from root
  .github/
    workflows/
      daily.yml       ← moved from root
  data/
    (created by first fetch)
```

---

## 4. Execution plan

### Phase 1: Foundation (no operator action needed)

| Step | What | Risk |
|---|---|---|
| 1.1 | Move files into correct folder structure | None |
| 1.2 | Create virtualenv, install `requirements.txt`, verify Python ≥ 3.10 | None |
| 1.3 | Update `fetch_p2p_price` in `fetch_rates.py` to use Bybit endpoint | Low — already tested the endpoint live |
| 1.4 | Run full fetch test, report all three premiums | Low |
| 1.5 | Serve page locally, verify chart renders, 375px layout, no console errors | None |

### Phase 2: Wallet (operator action needed)

| Step | What | Who |
|---|---|---|
| 2.1 | Run `new_wallet.py`, show operator the address only | Me |
| 2.2 | Fund the address with ~$5 ETH on Base (chain 8453) | **You** |
| 2.3 | Verify on-chain balance | Me |

### Phase 3: Attestation (no operator action needed)

| Step | What | Risk |
|---|---|---|
| 3.1 | Test `attest.py` with funded wallet | Low |
| 3.2 | Verify hash matches: rebuild SHA-256 from data, compare to on-chain calldata | None |

### Phase 4: Go live (operator action needed at two points)

| Step | What | Who |
|---|---|---|
| 4.1 | Delete placeholder data, run first real fetch + attest | Me |
| 4.2 | Create public GitHub repo or auth `gh` | **You** |
| 4.3 | Push project, add `ATTEST_PRIVATE_KEY` secret | **You** (or me if `gh` authed) |
| 4.4 | Enable Actions, trigger daily workflow manually, confirm full run | Me |
| 4.5 | Choose GitHub Pages or Vercel | **You** |
| 4.6 | Deploy, confirm live URL loads with real data | Me |
| 4.7 | Update README with live URL, changes log, first record date | Me |

---

## 5. Decisions needed from you

1. **Go ahead with Bybit as the P2P source?** (Tested and working, data shown above)
2. **GitHub Pages or Vercel for hosting?** (Can decide later but useful to know)
3. **Any concerns before I start Phase 1?**

---

## 6. Estimated effort

| Phase | Time |
|---|---|
| Foundation + Bybit integration | ~45 min |
| Wallet + attestation test | ~15 min (plus your funding time) |
| Deployment + live verification | ~30 min |
| **Total agent work** | **~1.5 hours** |

---

_This plan will be updated as work progresses. See `CHANGELOG.md` for a record of every change._
