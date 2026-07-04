# ResumeLab — AI Resume Analyzer

Upload a resume PDF and get an instant AI-powered review: an overall score out of 100, a list of detected skills, and three concrete tips to improve. Built with Streamlit and an OpenAI-compatible LLM backend (NVIDIA NIM).

## Features

- **Score (0–100)** — Overall resume quality at a glance, shown as a conic-gradient ring.
- **Skills detection** — Technical and soft skills surfaced as pills.
- **Improvement tips** — Three concrete, actionable suggestions.
- **Session history** — Every analysis in the current session is kept in the History tab.
- **Runs entirely in-memory** — No resume is ever written to disk.
- **Polished UI** — Custom CSS theme with a hero, nav bar, cards, and tabs.

## How it works

1. You upload a PDF resume in the **Upload** tab.
2. Text is extracted with `PyPDF2`.
3. The extracted text is sent to an OpenAI-compatible chat completions endpoint (default: NVIDIA NIM, model `meta/llama-3.1-70b-instruct`) with a system prompt instructing the model to return JSON with `score`, `skills`, and `tips`.
4. The response is parsed (with regex fallback to recover embedded JSON) and rendered as a score ring, skill pills, and a numbered tips list.
5. The result is stored in `st.session_state` and appended to the in-memory history.

## Project structure

```
resume-analyzer/
├── app.py              # Streamlit app + LLM call logic
├── requirements.txt    # Python dependencies
├── .env.example        # Template for your .env (safe to commit)
├── .env                # Your real secrets — gitignored, NEVER commit
├── .gitignore
└── .streamlit/
    └── config.toml     # Streamlit server config (headless, no telemetry)
```

## Setup

### 1. Clone

```powershell
git clone https://github.com/realganesh06-glitch/Resume-Analyzer.git
cd Resume-Analyzer
```

### 2. Create a virtual environment (recommended)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure your API key

Copy the template and fill in your values:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` and set:

| Variable | Description |
|---|---|
| `OPENAI_BASE_URL` | OpenAI-compatible base URL. Default: NVIDIA NIM. |
| `OPENAI_API_KEY`  | Your API key (REQUIRED). |
| `MODEL_ID`        | Model identifier. Default: `meta/llama-3.1-70b-instruct`. |

> The `.env` file is gitignored — it will not be committed.

### 5. Run

```powershell
python -m streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Configuration

All runtime configuration is read from environment variables (loaded from `.env` via `python-dotenv`):

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_BASE_URL` | `https://integrate.api.nvidia.com/v1` | LLM API base |
| `OPENAI_API_KEY` | _(none)_ | Bearer token |
| `MODEL_ID` | `meta/llama-3.1-70b-instruct` | Model to call |

The app will stop with a clear error if `OPENAI_API_KEY` is not set.

## Dependencies

- `streamlit` — UI framework
- `PyPDF2` — PDF text extraction
- `requests` — HTTP calls to the LLM API
- `python-dotenv` — `.env` loading

## Security notes

- **Never commit `.env`.** It is in `.gitignore` by default and contains your real API key.
- Resumes are processed in-memory only and are not persisted.

## License

This project is provided as-is for personal use.
