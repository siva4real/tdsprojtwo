---
title: LLM Analysis Quiz Solver
emoji: 🏃
colorFrom: red
colorTo: blue
sdk: docker
pinned: false
app_port: 7860
---

## LLM Analysis – Autonomous Quiz Solver

**An opinionated agent that chews through data-heavy quizzes with scraping, code execution, and cold-blooded automation.**

Built with FastAPI, LangGraph, Playwright, and Google's Gemini 2.5 Flash. Point it at a quiz URL, give it your secret, and let it run.

## What it does

- **Takes a quiz URL** via `POST /solve`
- **Scrapes and renders** JS-heavy pages
- **Downloads and inspects** files (PDF, CSV, images, etc.)
- **Writes and runs Python** for analysis and plots
- **Submits answers** back to the evaluation server until the chain ends

## Run it

- **Prereqs**: Python 3.12+, `uv` or `pip`, Docker (optional).

```bash
git clone https://github.com/23f3002766/tds-geniesolver.git
cd LLM-Analysis-TDS-Project-2

# with uv (recommended)
pip install uv
uv sync
uv run playwright install chromium
uv run main.py

# or plain Python
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -e .
playwright install chromium
python main.py
```

Server listens on `http://0.0.0.0:7860`.

## Configure it

Create a `.env` in the project root:

```env
EMAIL=your.email@example.com
SECRET=your_secret_string
GOOGLE_API_KEY=your_gemini_api_key_here
```

Get a Gemini API key from Google AI Studio and drop it into `GOOGLE_API_KEY`.

## Hit the API

- **Solve**:

```bash
curl -X POST http://localhost:7860/solve \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your.email@example.com",
    "secret": "your_secret_string",
    "url": "https://tds-llm-analysis.s-anand.net/demo"
  }'
```

Returns:

```json
{ "status": "ok" }
```

The agent runs in the background and walks the quiz chain on its own.

## Tools the agent uses

- **Web scraper – `get_rendered_html`**  
  Renders pages with Playwright (including heavy JavaScript), waits for network idle, and hands the LLM fully rendered HTML instead of half-baked DOM fragments.

- **File downloader – `download_file`**  
  Pulls down PDFs, CSVs, images, and other assets into `LLMFiles/` and returns the saved filename so the agent can inspect or parse them later.

- **Code executor – `run_code`**  
  Lets the LLM write Python, run it in an isolated subprocess, and read back stdout/stderr/exit code for data wrangling, stats, and plots.

- **HTTP submitter – `post_request`**  
  Sends JSON payloads to the quiz submission endpoints, parses responses, and avoids dumb resubmits when answers are wrong or time is up.

- **Dependency installer – `add_dependencies`**  
  Uses `uv add` to install Python packages on the fly so the agent can bring in whatever tooling it needs for a particular quiz (e.g., `pandas`, `matplotlib`, `scikit-learn`).

## Docker (optional)

```bash
docker build -t llm-analysis-agent .
docker run -p 7860:7860 \
  -e EMAIL="your.email@example.com" \
  -e SECRET="your_secret_string" \
  -e GOOGLE_API_KEY="your_api_key" \
  llm-analysis-agent
```

## License

MIT. See `LICENSE`.


