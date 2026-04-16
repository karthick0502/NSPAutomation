# NSP Cases — AI email enquiry workflow

End-to-end demo: customer **flight case** enquiry email → **OpenAI structured extraction** (dimensions, use case, requirements, summary, open questions) → **JSON** suitable for CRM, quoting, or CAD handoff.

## What’s included

| Piece | Purpose |
|--------|---------|
| `src/nsp_automation/` | Pydantic schema, prompts, email parsing, LLM call |
| `run.py` | CLI: process a `.txt` / `.eml` file, optional `--image` for vision |
| `server.py` | FastAPI `POST /extract` for **Make / Zapier** or any HTTP client |
| `sample_emails/enquiry_01.txt` | Realistic sample enquiry |

## Approach (for your Loom)

1. **Intake** — Raw email (or `.eml`) is normalised to plain text; optional images go to a vision-capable model together with the text.
2. **Reasoning** — One system prompt enforces “no invented dimensions,” separates **summary** vs **structured fields**, and surfaces **open_questions** for sales/engineering.
3. **Output** — A single Pydantic model is returned via OpenAI **structured outputs** (`chat.completions.parse`) so downstream systems get reliable JSON, not free-form prose.
4. **Automation** — The same logic is exposed over HTTP so orchestrators don’t duplicate prompts or parsing.

## Key decisions

- **OpenAI + `gpt-4o-mini` by default** — Good balance of cost, latency, and structured-output support; override with `OPENAI_MODEL`.
- **Structured outputs** — Reduces brittle JSON parsing and keeps the schema versioned in code (`models.py`).
- **Optional vision** — Attachments are supported in the CLI (`--image`) and API (base64 in JSON) without requiring a separate “attachment pipeline” for the demo.
- **HTTP API** — Triggers and scheduling live in your orchestrator; extraction stays in Python for testability and reuse in a larger system (queue workers, CRM webhooks).

## Setup

```bash
cd NSPAutomation
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Add `OPENAI_API_KEY` to `.env`.

## CLI

```bash
python run.py sample_emails/enquiry_01.txt
python run.py sample_emails/enquiry_01.txt --image sample_attachments/sketch.png
```

**Git Bash on Windows:** use forward slashes as above. A path like `sample_emails\enquiry_01.txt` is wrong in Bash because `\e` is treated as an escape, so the file becomes `sample_emailsenquiry_01.txt` and Python reports “File not found.” PowerShell and CMD accept both `\` and `/`.

### Logging

Logs go to **stderr**; the extracted JSON stays on **stdout** so you can pipe or redirect cleanly.

- Set `LOG_LEVEL` in `.env` (default `INFO`), or pass `--log-level DEBUG` on the CLI.
- The pipeline logs file load, body size, OpenAI model, latency, token usage (when returned), and high-level result metadata.

## HTTP API (automation)

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

- `GET /health` — liveness
- `POST /extract` — JSON body:

```json
{
  "email_text": "Plain body of the enquiry...",
  "images": [
    {
      "filename": "sketch.png",
      "mime_type": "image/png",
      "base64": "<base64>"
    }
  ]
}
```

Response: JSON matching the `EnquiryExtraction` schema (see `src/nsp_automation/models.py`).

## Suggested 5–10 minute Loom outline

1. Problem: flight-case enquiries are unstructured; quoting needs dimensions and constraints.
2. Show `sample_emails/enquiry_01.txt` and the schema in `models.py`.
3. Run `python run.py ...` and walk through the JSON (summary, dimensions, open_questions).
4. Show `server.py` and call `POST /extract` (e.g. curl or your automation tool) with the same JSON body as the CLI output.
5. Close with how you’d extend it: IMAP trigger, CRM ticket ID, human-in-the-loop approval, idempotent job queue.

## Integrating into a larger system

- Treat `POST /extract` as a **stateless microservice** behind a queue; store raw email + attachment refs in object storage, pass text + signed image URLs or base64.
- Version the Pydantic schema; emit **schema version** in API responses when you add fields.
- Use **open_questions** to route to sales vs engineering queues.
