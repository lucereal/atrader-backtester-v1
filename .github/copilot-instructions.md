# Copilot Instructions – Massive / Premarket Research

## Project Intent (Read First)
This project is for **premarket US equity research and ranking**, focused on **simple, iterative development**.

Primary goal:
- Take a candidate ticker list (e.g. from Finviz)
- Use **Massive (Polygon) REST APIs** to fetch data
- Rank tickers by likelihood of making a meaningful premarket move
- Keep logic explainable, debuggable, and incremental

This is **not** a high-frequency system and **not** using WebSockets at this stage.

---

## Data Source Rules
- Primary data source: **Massive (Polygon) Python client**
- The Massive python client is **installed in editable mode** and should be treated as the source of truth.
- Do **not** invent endpoints or parameters.
- Always search the workspace for existing client methods, examples, or docstrings before suggesting code.

### Explicitly NOT using (for now)
- WebSocket APIs
- Level 2 / order book data
- Complex async or streaming architectures

Prefer **REST snapshots, aggregates, and reference endpoints** only.

---

## Workspace Tools You Have Access To
You should assume the following are available and should be referenced when helpful:

1. **Editable Massive Python Client**
   - Installed via `pip install -e`
   - Source code and docstrings are available in the workspace
   - Prefer idiomatic usage shown in this client

2. **Community / MCP Repository**
   - Contains examples, tool definitions, and usage patterns
   - Use as reference documentation and examples
   - Do not assume it is installed as a runtime dependency unless explicitly stated

3. **Scratch Pad Folder**
   - Contains files intended for experimentation and testing
   - Safe place to prototype code, explore API responses, and iterate
   - Production logic should eventually be moved out of scratch files

4. **Rest API Docs**
   - Contains files that describe the Massive REST API endpoints
   - Use as reference for endpoint parameters and response structures
   - Use to figure out which endpoints to use for specific data needs

---

## Development Philosophy
- Start simple, then layer complexity
- Prefer clarity over cleverness
- Avoid premature abstraction
- Write code that is easy to inspect and reason about

If a solution feels “over-engineered”, it probably is.

---

## Time and Market Assumptions
- Market: US equities
- Focus: **Premarket**
- All times should be treated consistently (call out timezone assumptions explicitly when relevant)
- Be careful with premarket vs regular-session distinctions

---

## How to Respond as Copilot
When asked for help:
1. Prefer searching the workspace over guessing
2. Reference existing examples or client code when possible
3. Keep answers scoped to the current iteration (V1 simplicity)
4. Ask clarifying questions **only if necessary to avoid wrong assumptions**

Do not:
- Hallucinate unavailable data
- Suggest WebSockets unless explicitly requested
- Skip over available workspace context

---

## Current Stage (Important)
We are in **early iteration mode**.

The objective right now is:
> “Get a clean, reliable pipeline from ticker list → REST data → simple ranking.”

Optimization, automation, and real-time concerns come later.


## Data Requirements Roadmap (Massive / Polygon)

This project intentionally pulls **only the data needed for the current iteration**.
Do not fetch or design for future stages prematurely.

---

## V1 — Premarket “In-Play” Ranking (Core)

**Goal:**  
From a candidate ticker list, rank which tickers are:
- most likely to move soon
- and are actually tradable

Answering:
> “Which of these tickers deserves attention right now?”

### Data to Pull (Required)

#### 1. Ticker Identity / Reference
- Ticker symbol
- Company name
- Exchange

Purpose:
- Logging
- Sanity checks
- Human-readable outputs

Source:
- Massive reference / ticker details endpoints

---

#### 2. Previous Day Context
- Previous close
- Previous day high
- Previous day low
- Previous day volume

Purpose:
- Gap % calculation
- Baseline context
- Avoid ranking already-exhausted names

Source:
- Daily aggregates (1d)

---

#### 3. Premarket Price State
- Last trade price (premarket)
- Premarket high
- Premarket low
- Premarket cumulative volume (or proxy)

Purpose:
- Detect price expansion
- Identify active vs stagnant tickers
- Core momentum context

Source:
- Intraday aggregates (premarket window)
- Snapshot endpoint

---

#### 4. Liquidity / Tradability
- Current bid
- Current ask
- NBBO spread
- (Optional) bid/ask size if available

Purpose:
- Filter out illiquid / trap tickers
- Prefer names that can actually be traded

Source:
- Snapshot (quotes)

---

#### 5. Activity / Urgency Signals
- Trade count (or proxy)
- Volume per minute (approximate)
- Time since last trade

Purpose:
- Distinguish “about to move” from “already moved”
- Capture early momentum

Source:
- Aggregates + last trade snapshot

---

#### 6. Derived Metrics (Computed, Not Pulled)
- Gap %
- Premarket range %
- Dollar volume
- Spread %
- Simple composite score

Purpose:
- Ranking logic
- Explainability

---

### Explicitly Excluded in V1
- WebSockets
- Level 2 / order book
- Tick-by-tick tape analysis
- Machine learning models
- Async / streaming infrastructure

---

## V2 — Context & Confidence Layer

**Goal:**  
Explain *why* a ticker is moving and reduce false positives.

Answering:
> “Why is this moving, and should I trust it?”

---

### Additional Data to Pull

#### 7. News / Catalyst Presence
- Recent news exists (yes/no)
- Headline
- Publish timestamp
- Source
- Article URL

Purpose:
- Distinguish catalyst-driven moves from random pops
- Increase confidence in holding winners

Source:
- Massive ticker news endpoint

Notes:
- Full article text is not required
- Sentiment analysis is optional and not required in V2

---

#### 8. Volatility Context
- Recent intraday range
- ATR or range expansion vs baseline (computed)

Purpose:
- Avoid ranking low-volatility names
- Normalize behavior across price levels

Source:
- Aggregates (computed client-side)

---

#### 9. Relative Strength (Optional)
- Ticker return vs SPY / QQQ (same window)

Purpose:
- Avoid weak names in strong market tape
- Add market context to rankings

Source:
- Same aggregate endpoints for index symbols

---

## V3 — Feedback & Learning (Later)

**Goal:**  
Measure outcomes and improve ranking quality over time.

Answering:
> “Did my ranking actually work?”

---

### Data to Track (Internal, Not Massive)
- Did price break premarket high?
- Did it reach 1R / target?
- Time to first meaningful move
- Max favorable excursion (MFE)
- Max adverse excursion (MAE)

Purpose:
- Expectancy analysis
- Rule refinement
- Future automation

Notes:
- This stage uses stored outputs and trade results
- Does not require new Massive endpoints

---

## Design Principles
- Pull the minimum data needed for the current version
- Prefer REST snapshots and aggregates
- Promote complexity only after V1 ranking is trusted
- Avoid designing for WebSockets until explicitly required

Current active stage: **V1**
