# HireMe AI 🚀
> **AI job platform & ATS-optimized resume tailor**

HireMe AI is a full-stack career platform engineered specifically for **freshers and early-career software engineers (0–2 years experience)**. It combines an authentic multi-source job ingestion pipeline with a **truthful, minimal-edit ATS resume tailoring engine** that strictly forbids hallucinated metrics or fabricated technologies.

---

## ✨ Key Features

### 1. 🎯 Curated Fresher Job Aggregator & Funnel
- **Direct Company ATS Ingestion**: Scrapes real-time postings directly from Greenhouse, Lever, and Ashby boards for top tech companies, plus open aggregators (Remotive, Arbeitnow, Adzuna, Jobicy, Himalayas).
- **3-Stage Fresher Quality Funnel**:
  1. *Hard-Reject Filter*: Automatically drops senior, lead, principal, and 3+ years experience roles.
  2. *LLM Classifier*: Evaluates role expectations, educational requirements, and entry-level accessibility.
  3. *Composite Scoring*: Computes an authentic `fresher_score` prioritizing truly accessible junior roles.
- **Direct Apply Links**: Every job post includes verified, direct application links.

### 2. 📄 Truthful "Minimal-Edit" ATS Resume Tailoring
- **Facts Store Single Source of Truth**: The candidate's original CV is treated as an immutable ground-truth facts database.
- **Allowed Edit Operations Only**:
  - `SELECT / DROP`: Prioritize relevant bullets and prune filler.
  - `REORDER`: Move highest-impact matching items to the top.
  - `TRIM`: Cut wordy bullets down to their core impact.
  - `VERB_SWAP`: Upgrade weak openers (*"worked on"*, *"helped in"*) to strong action verbs (*"Built"*, *"Engineered"*, *"Optimized"*).
  - `TERM_ALIGN`: Align terminology strictly matching the JD (*"postgres"* ➔ *"PostgreSQL"*).
  - `KEYWORD_ADD`: Add keywords only when substantiated by candidate facts or explicit technology implication maps.
  - `MERGE`: Combine short, related bullet points.
- **Zero-Fabrication Guarantee**: Never invents metrics, percentages, dates, tools, degrees, or roles.
- **Jake's Resume LaTeX Template**: Clean, single-column, standard ATS-parsed formatting compiled via `tectonic` or `pdflatex` with 1-page line budget enforcement and PyMuPDF layout verification.

### 3. 👤 Visual Candidate Facts Studio
- Visual editor for Personal Info, Verified Technical Skills (badge chips), Work Experiences, Projects, and Education.
- Direct JSON inspection toggle for power users.
- Live database persistence so candidate facts are preserved and never lost across sessions.

### 4. 🔒 Production Authentication & Data Persistence
- **Email & Password Authentication**: Secure password hashing with `bcrypt` (12 rounds) and signed `JWT` access tokens with expiration.
- **Guest-to-User Profile Claiming**: Resumes uploaded before logging in are automatically adopted and claimed upon registration or login.
- **User Ownership**: Every profile, tailored resume PDF version, and job application tracking state is permanently saved to your relational account.

---

## 🏗️ Project Architecture

```
naukri/
├── ai_job_platform/           # FastAPI Backend Service
│   ├── app/
│   │   ├── core/              # Config, DB connection, JWT security & bcrypt
│   │   ├── models/            # SQLAlchemy async models (SQLite / PostgreSQL)
│   │   ├── schemas/           # Pydantic validation schemas & DTOs
│   │   ├── services/          # LLM pipeline, Tailor engine, ATS verifier, Ingestion
│   │   └── routers/           # HTTP API routes (auth, jobs, resume, profiles, applications)
│   ├── tests/                 # Full pytest suite (auth, pipeline, classifier, LLM)
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Backend environment template
│
├── frontend_job/              # React + Vite Frontend Application
│   ├── src/
│   │   ├── api/               # Axios client with JWT bearer interceptors
│   │   ├── context/           # AppContext (global auth state, active profile)
│   │   ├── components/        # Navbar, AuthModal (React Portal), UI components
│   │   └── pages/             # Landing/Upload, Jobs, JobDetail, Applications, Profile Studio
│   ├── package.json           # Frontend dependencies
│   └── vite.config.js         # Vite configuration (port 3000)
│
└── .gitignore                 # Comprehensive secrets & build artifact filter
```

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python**: 3.11+
- **Node.js**: 18+ and npm
- **Groq API Key**: (Free at [console.groq.com](https://console.groq.com))
- *(Optional)* **Tectonic** or **pdflatex**: For local server-side PDF compilation. (If not installed, LaTeX source is always available to download and preview).

---

### 1. Backend Setup

```bash
# Navigate to the backend directory
cd ai_job_platform

# Create and activate virtual environment
python -m venv venv

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Edit `.env` and fill in your keys:
```env
APP_NAME="HireMe AI"
APP_ENV=development
DEBUG=true

# Database (defaults to zero-config SQLite)
DATABASE_URL=sqlite+aiosqlite:///./ai_job_platform.db

# Groq LLM Key
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# JWT Authentication
JWT_SECRET_KEY=your_random_secret_jwt_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_DAYS=7
```

Start the FastAPI backend server:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API docs will be live at `http://127.0.0.1:8000/docs`.

---

### 2. Frontend Setup

Open a separate terminal window:
```bash
# Navigate to the frontend directory
cd frontend_job

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 🧪 Running Tests

Run the backend unit and integration test suite:

```bash
cd ai_job_platform
python -m pytest tests/test_auth.py tests/test_llm.py tests/test_classifier.py -v
```

---

## 📡 Core API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register new user with email and password |
| `POST` | `/api/v1/auth/login` | Login and receive signed JWT access token |
| `GET` | `/api/v1/auth/me` | Fetch active user session & latest profile ID |
| `POST` | `/api/v1/resume/upload` | Upload & parse resume into ground-truth facts |
| `POST` | `/api/v1/resume/tailor` | Minimal-edit ATS resume tailoring against target JD |
| `GET` | `/api/v1/resume/my-versions` | List all tailored resume versions for user |
| `GET` | `/api/v1/resume/download/{id}` | Download generated resume PDF |
| `GET` | `/api/v1/profiles/me` | Retrieve authenticated user's current profile |
| `PATCH` | `/api/v1/profiles/{id}` | Update candidate facts store (skills, experience, etc.) |
| `POST` | `/api/v1/profiles/{id}/claim` | Claim guest-uploaded profile to authenticated user |
| `GET` | `/api/v1/jobs` | Search & filter fresher-verified jobs |
| `GET` | `/api/v1/applications/{profile_id}` | Retrieve tracked job applications & statuses |

---

## 🛡️ Security & Privacy
- **Password Protection**: Passwords are never stored in plaintext; hashed with bcrypt (12 rounds).
- **Protected Environment**: Sensitive `.env` keys, personal resume uploads, and database files are excluded from Git via `.gitignore`.
- **Zero Fabrication**: LLM prompts explicitly forbid adding non-existent tools, false metrics, or hallucinated claims to candidate resumes.

---

## 📄 License
MIT License. Built for job seekers and early career software engineers.
