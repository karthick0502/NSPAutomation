# NSP Cases — AI email enquiry workflow

End-to-end demo: customer **flight case** enquiry email → **OpenAI structured extraction** (dimensions, use case, requirements, summary, open questions) → **JSON** suitable for CRM, quoting, or CAD handoff.

## What’s included

| Piece | Purpose |
|--------|---------|
| `src/nsp_automation/` | Pydantic schema, prompts, email parsing, LLM call |
| `run.py` | CLI: process a `.txt` / `.eml` file, optional `--image` for vision |
| `server.py` | FastAPI `POST /extract` for **Make / Zapier** or any HTTP client |
| `sample_emails/enquiry_01.txt` | Realistic sample enquiry |

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
