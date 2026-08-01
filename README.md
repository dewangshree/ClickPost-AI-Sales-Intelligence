# ClickPost AI Sales Intelligence

An end-to-end buying-intent prototype for ClickPost's outbound sales motion: it searches the public web for signal on target D2C accounts, extracts structured buying-intent signals with an LLM, scores/ranks accounts with a transparent rule-based model, and generates a personalized LinkedIn + email sequence for the top 5 accounts — grounded in the exact signal captured.

Built for the ClickPost AI Sales Intelligence take-home. See [`MEMO.md`](./MEMO.md) for the signal taxonomy, methodology, and tradeoffs write-up.

## What it does

```
brands.csv
    │
    ▼
┌─────────────────┐     Tavily web search (funding / hiring / expansion /
│  SearchService   │────  shipping & returns complaints / competitor tech
└─────────────────┘      stack / Trustpilot / Reddit)
    │
    ▼
┌─────────────────┐     Groq (llama-3.1-8b-instant), JSON-mode structured
│  SignalService   │────  extraction → typed Signal objects with evidence
└─────────────────┘      + source URLs + confidence
    │
    ▼
┌─────────────────┐     Rule-based weighted scoring (0–100), priority
│  ScoringService  │────  tier (High/Medium/Low), human-readable reasoning
└─────────────────┘
    │
    ▼
   Rank all accounts → take Top 5
    │
    ▼
┌─────────────────┐     Groq-generated LinkedIn message + follow-up email,
│ OutreachService  │────  explicitly grounded in the captured signal
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  ExportService   │──── output/ranked_accounts.csv, signals.json, top5_outreach.json
└─────────────────┘
```

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Web search | [Tavily](https://tavily.com) | Free-tier-friendly search API with clean structured results, no scraping/ToS risk |
| Signal extraction & outreach generation | [Groq](https://groq.com) (`llama-3.1-8b-instant`) | Fast, free-tier inference, native JSON-mode for reliable structured output |
| Scoring | Rule-based Python (no LLM) | Explainable, deterministic, defensible to a sales leader — not a black box |
| Data validation | Pydantic v2 | Typed, self-documenting schemas across every pipeline stage |
| UI | Gradio | Zero-boilerplate way to upload a CSV and download results without building a UI |

## Project structure

```
clickpost-ai/
├── main.py                    # CLI entry point — runs the full pipeline
├── app.py                     # Gradio UI — upload CSV, run pipeline, download outputs
├── config.py                  # Env var loading + logging setup
├── models.py                  # Pydantic schemas (Signal, ScoredAccount, RankedAccount, Outreach)
├── brands.csv                 # Sample account list (the 25 brands from the brief)
├── prompts/
│   ├── signal_prompt.txt      # System prompt for signal extraction
│   └── outreach_prompt.txt    # System prompt for outreach generation
├── services/
│   ├── search_service.py      # Tavily search, 3 retries with backoff
│   ├── signal_service.py      # Groq structured extraction
│   ├── scoring_service.py     # Weighted rule-based scorer
│   ├── outreach_service.py    # Groq outreach generation
│   └── export_service.py      # CSV/JSON exporters
└── requirements.txt
```

## Setup

**1. Clone and enter the project**
```bash
git clone https://github.com/dewangshree/ClickPost-AI-Sales-Intelligence.git
cd ClickPost-AI-Sales-Intelligence/clickpost-ai
```

**2. Create a virtual environment and install dependencies**
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Add API keys**
```bash
cp .env.example .env
```
Fill in:
```
GROQ_API_KEY=your_groq_key      # free tier: https://console.groq.com
TAVILY_API_KEY=your_tavily_key  # free tier: https://tavily.com
```
Both providers offer generous free tiers, matching the assignment's no-paid-tools constraint.

## Usage

**Option A — CLI (fastest way to reproduce results)**
```bash
python main.py
```
Runs the full pipeline against `brands.csv` and writes results to `output/`.

**Option B — Gradio UI (for demoing / uploading a different account list)**
```bash
python app.py
```
Opens a local browser window. Upload any `company,website,industry` CSV, click **Start Processing**, and download the three output files directly from the UI.

## Input format

`brands.csv`:
```csv
company,website,industry
Chubbies,https://www.chubbiesshorts.com,Apparel & Lifestyle
...
```

## Output

Written to `output/` after a run:

| File | Contents |
|---|---|
| `ranked_accounts.csv` | Every account, ranked, with score (0–100), priority tier, confidence, and a plain-English reason string |
| `signals.json` | Raw signal extraction per account — signal type, description, evidence snippet, source URL, confidence |
| `top5_outreach.json` | LinkedIn message + follow-up email for each of the Top 5 accounts, grounded in their specific captured signal |

> Sample run outputs aren't checked into this repo (API keys are required and outputs shouldn't be faked). Run the pipeline once with your own keys to generate a live sample set — [`MEMO.md`](./MEMO.md) documents the reasoning independent of any single run.

## Design notes & known limitations

- **Scoring is intentionally rule-based, not an LLM judge.** The brief calls for a scoring system a sales leader can trust or push back on — a fixed, inspectable weight table (see `scoring_service.py`) is easier to defend than an opaque model score. Full reasoning in `MEMO.md`.
- **Rate limiting:** the pipeline sleeps ~10s between Groq calls to stay within free-tier limits, so a full 25-account run takes several minutes — this is a deliberate reliability-over-speed tradeoff, not a bug.
- **Search depth is capped** (`search_depth="basic"`, 3 results/query) to stay within Tavily's free tier. Coverage is therefore partial for some accounts by design — see the memo for what a paid enrichment tier would unlock.
- **Failure handling:** if search or extraction fails for a given company, the pipeline logs the error and continues rather than crashing the batch (see `main.py`'s per-account try/except).

## License

MIT
