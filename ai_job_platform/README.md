# HireMe AI — Backend Service
> AI Job Platform & ATS-Optimized Resume Tailor

A production-grade, full-stack AI career platform specifically engineered for **freshers and entry-level engineers (0–2 years experience)**.

Features:
- **Verified Multi-Source Job Ingestion**: Pulls from Direct Company ATS boards (Greenhouse, Lever, Ashby for 50+ tech companies hiring in India) + Open aggregators (Adzuna, Jooble, JSearch, Careerjet, Remotive, Arbeitnow, The Muse, Himalayas).
- **3-Stage Fresher Quality Funnel**: Strict rule-based hard rejects (senior/lead titles, >2 years exp requirements, team-leading phrases) + Batched LLM classification + composite scoring.
- **Direct Apply Links**: Every job listing provides an authentic, working direct application URL.
- **Truthful LaTeX Resume Tailoring**: 9-stage pipeline rendering single-column Jake's Resume style templates, with strict STAR rewriting that forbids invented metrics or tools, automated 1-page line budget enforcement, and PyMuPDF ATS verification.
- **Swappable LLM Architecture**: Powered by Groq using `openai/gpt-oss-120b` (with automated exponential backoff and schema retries) with swappable Google Gemini fallback.

---

## 🏗️ Architecture Overview

```
ai_job_platform/
├── app/
│   ├── core/              # Config, DB connection, logging middleware
│   ├── models/            # SQLAlchemy async DB models (dual SQLite/Postgres compatible)
│   ├── schemas/           # Pydantic validation schemas & DTOs
│   ├── services/
│   │   ├── llm.py         # Swappable GroqProvider & GeminiProvider
│   │   ├── job_classifier.py  # 3-Stage Fresher Funnel (Rule, LLM, Fresher Score)
│   │   ├── job_aggregator.py  # Concurrent multi-source fetch, RapidFuzz deduplication
│   │   ├── job_sources/   # Modular adapters (Greenhouse, Lever, Ashby, Adzuna, etc.)
│   │   ├── facts_store.py # Canonical candidate ground-truth facts store
│   │   ├── jd_analyzer.py # Structured JD keyword extractor with hashing cache
│   │   ├── latex_renderer.py  # Jake's Resume single-column Jinja2 template & 1-page auto-trim
│   │   ├── latex_compiler.py  # Async subprocess runner for Tectonic / pdflatex
│   │   ├── ats_verifier.py    # PyMuPDF ATS heading & layout verification
│   │   └── resume_tailor_pipeline.py # 9-step LaTeX ATS master tailoring pipeline
│   └── routers/           # FastAPI endpoints (jobs, resume, profiles, applications)
├── prompts/               # Versioned text prompts with few-shot examples
├── tests/                 # Full pytest suite (LLM, Sources, Classifier, Pipeline, Integration)
└── Dockerfile             # Standalone container with Tectonic & fonts preinstalled
```

---

## 🚀 Quickstart & Setup

### Option 1: Running with Docker (Recommended for Resume PDF Compilation)

The Dockerfile packages Python 3.11, all dependencies, and the `tectonic` modern LaTeX typesetting engine:

```bash
# Build the Docker image
docker build -t ai-fresher-platform .

# Run the container (mounts your .env file)
docker run -p 8000:8000 --env-file .env ai-fresher-platform
```

Visit `http://localhost:8000/docs` to explore the interactive API.

---

### Option 2: Running Locally

#### 1. Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend)
- (Optional) `tectonic` or `pdflatex` for local PDF compilation. If not installed, the platform generates and provides the clean `.tex` LaTeX source and preview automatically.

#### 2. Backend Setup
```bash
cd ai_job_platform

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and supply your GROQ_API_KEY

# Start backend server
uvicorn app.main:app --reload --port 8000
```

#### 3. Frontend Setup
```bash
cd frontend_job
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 🖨️ How to Install Tectonic Locally

`tectonic` is a self-contained, modern, lightning-fast XeTeX engine that downloads packages on the fly without needing a multi-gigabyte TeX Live distribution.

- **macOS (Homebrew)**:
  ```bash
  brew install tectonic
  ```
- **Linux (Ubuntu/Debian)**:
  ```bash
  curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.tectonic-typesetting.net | sh
  sudo mv tectonic /usr/local/bin/
  ```
- **Windows (Cargo or Direct Binary)**:
  - If Rust/Cargo is installed:
    ```bash
    cargo install tectonic
    ```
  - Or download `tectonic.exe` from [Tectonic GitHub Releases](https://github.com/tectonic-typesetting/tectonic/releases) and place it on your system `PATH`.

---

## 🎯 Scoring & Ranking Algorithm

Every job card is scored and ranked by a composite formula:
$$\text{Composite Rank} = \text{Fresher Score} \times \text{Match Percentage}$$

### 1. Fresher Score (0–100 Points)
- **Seniority Fit (0–40 pts)**:
  - `intern`: 40
  - `entry`: 40
  - `junior`: 35
  - `mid`: 10
  - `senior` / `lead`: 0 (rejected in Stage 1)
- **Years of Experience Fit (0–25 pts)**:
  - 0–1 year: 25
  - 1–2 years: 20
  - Unspecified / fresh graduates: 15
  - >2 years: 0 (rejected in Stage 1)
- **Explicit Fresher Title Signals (+10 pts)**:
  - Boosted if title contains `intern`, `trainee`, `graduate`, `GET`, `entry-level`, `junior`, `fresher`, `campus`, `2025/2026 batch`.
- **Candidate Skill Overlap (0–20 pts)**:
  - Normalized candidate skills matched against required skills ($2\times$ weight) and nice-to-have skills ($1\times$ weight).
- **Posting Freshness (0–5 pts)**:
  - Posted $\le 48\text{h}$: 5 pts
  - Posted $\le 7\text{d}$: 3 pts
  - Posted $\le 14\text{d}$: 1 pt

Threshold: Any job with `fresher_score < 60` is automatically excluded from the recommendations feed.

---

## 🔌 How to Add a New Job Source Adapter

Adding a new job board adapter is straightforward thanks to the unified `JobSource` interface:

1. Create a new adapter file in `app/services/job_sources/<source_name>.py`:
   ```python
   from app.services.job_sources.base import JobSource, RawJob, clean_html_text

   class MyNewJobSource(JobSource):
       name = "mynewsource"

       async def fetch_jobs(self, limit: int = 50) -> List[RawJob]:
           # 1. Fetch raw data using httpx.AsyncClient
           # 2. Extract and sanitize fields (clean_html_text, is_valid_http_url)
           # 3. Return List[RawJob]
           pass
   ```
2. Add a toggle and any API credentials in `app/core/config.py`:
   ```python
   ENABLE_MYNEWSOURCE: bool = True
   MYNEWSOURCE_API_KEY: Optional[str] = None
   ```
3. Register the class in `app/services/job_sources/__init__.py`. The `JobAggregator` will automatically fetch, deduplicate (via RapidFuzz), and schedule synchronization!

---

## 🧪 Running Tests

The test suite covers all units and end-to-end flows:

```bash
cd ai_job_platform
python -m pytest tests/ -v
```

Tests include:
- `tests/test_llm.py`: Provider extraction, schema validation retries.
- `tests/test_job_sources.py`: HTML stripping, apply URL verification, RapidFuzz deduplication.
- `tests/test_classifier.py`: 37+ labeled job cases, experience extraction, senior rejection rules.
- `tests/test_resume_pipeline.py`: Canonical facts store, Jake's LaTeX rendering, ATS verification.
- `tests/test_integration_flow.py`: Complete candidate-to-PDF integration pipeline.
