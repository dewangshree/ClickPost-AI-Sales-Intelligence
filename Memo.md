# ClickPost AI Sales Intelligence — Project Memo

**Author:** Shreyas Vikrant Dewangswami
**Repo:** `ClickPost-AI-Sales-Intelligence`

---

## 1. Signal Taxonomy & Reasoning

ClickPost sells a post-purchase / returns / logistics-intelligence platform. The buyer is usually a CX Head, Head of Ops, CTO, or Founder at a $5–100M GMV D2C brand. For that buyer, "buying intent" isn't just *the company is doing well* — it's *the company is currently feeling logistics/post-purchase pain, and has budget and organizational appetite to fix it right now*. That distinction drove the weighting below (`services/scoring_service.py`):

| Signal type | Weight | Why this weight |
|---|---|---|
| Shipping complaints | **30** | Direct, first-party evidence of the exact pain ClickPost solves (WISMO, delivery exceptions, NDR). This is the strongest possible signal — the buyer is already unhappy with their current stack. |
| Returns complaints | **30** | Same logic — return friction, refund delays, and RTO issues sit squarely in ClickPost's product. Public complaints here are close to a hand-raise. |
| Competitor / tech-stack signal (Loop, AfterShip, Redo, Onward) | **25** | Confirms the account already has budget allocated to this exact problem category and an existing vendor relationship that can be displaced. High intent, but slightly softer than an active complaint because a happy incumbent customer scores the same as an unhappy one on this signal alone. |
| Funding | **20** | Correlates with willingness to spend on tooling, but is a *generic growth* signal — plenty of well-funded brands have no post-purchase pain yet. Included because it's a legitimate trigger (new budget), not because it's diagnostic of the specific problem. |
| Hiring (Returns Manager, Logistics Ops, CX Platform Lead) | **20** | A stronger proxy than funding — hiring for a role that owns this exact problem suggests the org is actively organizing around it — but it's still a leading indicator, not a confirmed pain point. |
| Expansion (new SKUs, geo expansion, new warehouses) | **15** | GMV inflection often precedes logistics pain, per the brief, but it's the most indirect signal in the set — expansion doesn't guarantee the current stack is straining yet. |
| Other detected signal | **10** | Catch-all floor so any evidence-backed signal the LLM surfaces still contributes, without letting unclassified signals dominate the score. |

Score is capped at 100 to prevent a single account with many small signals from appearing more "intent-ready" than an account with one severe, high-confidence complaint signal.

**Deliberate exclusion:** "raised funding" alone was *not* made a dominant weight, on purpose — the brief specifically calls out that generic growth signals shouldn't be conflated with real buying intent. A funded company with a smooth post-purchase experience is not a priority account; a company with public shipping complaints is, regardless of funding stage.

## 2. Methodology

1. **Search (`SearchService`)** — one Tavily query per account, deliberately built as a single OR-clause covering funding, hiring, expansion, shipping/returns complaints, named competitors, and review/forum sources (Trustpilot, Reddit). This maximizes signal coverage per API call given the free-tier, no-paid-enrichment constraint in the brief.
2. **Extraction (`SignalService`)** — Groq (`llama-3.1-8b-instant`) reads the raw search snippets and returns strict JSON: signal type, description, the evidence string, source URL, and a confidence score. Forcing JSON-mode output (rather than parsing free text) makes the extraction step deterministic and pipeline-safe.
3. **Scoring (`ScoringService`)** — plain Python, not an LLM call. See the weight table above. Every score comes with a human-readable `reason` string built directly from the matched signal types, so the "why" is always visible next to the number.
4. **Ranking** — accounts are sorted by score descending; ties are broken by insertion order (stable sort), which is acceptable at this scale but is called out as a gap in §4.
5. **Activation (`OutreachService`)** — for the Top 5 only, Groq generates one LinkedIn message and one follow-up email per account, using the account's own captured signals (type + description) as the only grounding context — no generic template filler. The prompt explicitly forbids generic outreach and requires the message to reference the detected signal.
6. **Export (`ExportService`)** — three files written to `output/`: the full ranked list (CSV, easy to open in Sheets for a sales leader), the raw signal extractions (JSON, for auditability), and the Top 5 outreach sequences (JSON).

## 3. Key Tradeoffs

- **Rule-based scoring over LLM-as-judge.** Chose explainability over nuance. An LLM judge could weigh interacting signals more cleverly (e.g., "hiring + expansion together is stronger than either alone"), but a sales leader can't easily audit or contest a black-box score. The weight table can be argued with in a five-minute conversation — that mattered more here than marginal scoring accuracy.
- **One search query per account, not one per source.** Querying G2, Trustpilot, and Reddit separately per account would give deeper per-source coverage, but at 3x the API calls per account with a free-tier budget. Given the assignment's explicit no-paid-tools constraint, I optimized for broad coverage across 25 accounts over deep coverage of fewer accounts.
- **`llama-3.1-8b-instant` over a larger model.** Free-tier Groq rate limits make a bigger model impractical for a 25-account batch job with three sequential Groq calls (extraction, and later outreach) per account. The tradeoff is some loss of extraction nuance on ambiguous search snippets, mitigated by requiring the model to also emit a `confidence` score and a `reasoning` field, so low-confidence extractions are visible rather than silently trusted.
- **Sequential processing with rate-limit sleeps**, not concurrent/async. Prioritizes not getting rate-limited mid-batch over runtime — a full run takes several minutes rather than seconds. For a 25-account prototype this is an acceptable tradeoff; it would not scale to thousands of accounts without moving to a queue-based/async architecture.
- **No independent GMV verification**, per the assignment's own instructions — all 25 brands are assumed to qualify for ClickPost's ICP band unless search results surfaced clear evidence otherwise.

## 4. Data-Sourcing & Compliance Considerations

- Tavily is used instead of direct scraping specifically to avoid ToS violations against G2, Trustpilot, and LinkedIn — Tavily aggregates already-public search results rather than scraping protected pages directly.
- LinkedIn itself is never queried or scraped directly (its ToS prohibits automated scraping); hiring signals come through general web search of job postings, not LinkedIn's own API/pages.
- Outreach messages are generated as drafts only — the pipeline does not auto-send LinkedIn messages or emails. A human SDR is assumed to review and send, which is also a reasonable compliance and quality-control checkpoint before anything reaches a real prospect.
- Because free-tier search returns thin snippets, some accounts may show `confidence: 0.0` with no signals if Tavily returned nothing useful. The pipeline is built to continue past this (per-account try/except in `main.py`) rather than fail the whole batch — partial coverage with honest low-confidence flags, not silent gaps.

## 5. What I'd Build Next With More Time or Data

- **Official job-board APIs** (Greenhouse, Lever, Ashby public job listings) for hiring signals instead of generic web search — much higher precision on "is this company hiring a Returns Manager right now."
- **Licensed review-platform access** (G2/Trustpilot APIs) for complaint signals — free-tier search snippets are noisy; a real review API would let me quote specific, dated complaints rather than inferring from a search snippet.
- **Time-decay weighting** — a shipping complaint from last week should outscore one from two years ago. Currently the model treats all evidence as equally fresh.
- **Multi-source corroboration boost** — if the same signal (e.g., "uses Loop Returns") is confirmed by two independent sources, that should raise confidence and score more than either source alone.
- **Feedback loop from actual SDR outcomes** — track reply/meeting-booked rates by signal type and let the weight table be recalibrated empirically instead of staying a fixed heuristic forever.
- **Concurrency** — move the per-account loop to async/batched Groq + Tavily calls (with proper rate-limit handling) so a 25-account run takes under a minute instead of several.

This is deliberately a thoughtful prototype on a handful of accounts, not a production-claiming system — see the README's Known Limitations section for what's explicitly out of scope today.
