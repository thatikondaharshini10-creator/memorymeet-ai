# MemoryMeet — AI Meeting Prep Agent with Long-Term Memory

**MemoryMeet** is an intelligent AI meeting preparation and memory synthesis agent built for hackathon velocity. It processes meeting recordings, extracts key facts, participant decisions, and commitments, stores them into **Hindsight** biomimetic long-term memory banks, and generates high-context prep briefs for future meetings.

---

## Architecture Flow

```
Meeting Recording (Audio/Video) or Transcript Fallback
  → Speech-to-Text (Gemini Multimodal / OpenAI Whisper)
  → Meeting Transcript
  → AI Memory Extraction Agent (LLM)
  → Hindsight Long-Term Memory Bank (Retain)
  → Long-Term Memory Priming & Hybrid Retrieval (Recall)
  → Meeting Preparation Agent
  → Personalized Executive Meeting Brief
```

---

## Project Structure

```
first-ai-project/
├── .env.example                 # Configuration template with API key slots
├── requirements.txt             # Python backend dependencies
├── README.md                    # Project documentation & run guide
│
├── backend/
│   └── app/
│       ├── __init__.py          # Package initializer
│       ├── main.py              # FastAPI entrypoint, CORS, and static mount
│       ├── core/
│       │   ├── __init__.py
│       │   └── config.py        # Pydantic environment configuration
│       ├── db/
│       │   ├── __init__.py
│       │   └── database.py      # SQLite connection & metadata tables
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes.py        # API routes (/api/health, etc.)
│       └── services/
│           ├── __init__.py      # Service registry
│           ├── transcription_service.py # Speech-to-Text interface (Phase 2)
│           ├── memory_service.py        # Hindsight memory interface (Phase 2)
│           ├── ai_service.py            # LLM extraction & prep interface (Phase 2)
│           └── meeting_service.py       # Pipeline coordinator (Phase 2)
│
└── frontend/
    ├── index.html               # Responsive single-page UI
    ├── style.css                # Glassmorphism dark design system
    └── app.js                   # Client-side backend communication logic
```

---

## Quick Start & Running the Project

### 1. Prerequisites
* Python 3.10+ (Current environment uses Python 3.13.7)
* Pip

### 2. Activate Virtual Environment
```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment
```powershell
copy .env.example .env
```

### 5. Launch the Server
```powershell
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Access the Application
* **Frontend Web Dashboard:** [http://localhost:8000](http://localhost:8000)
* **Backend API Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)
* **Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Phase 1 Verification

Phase 1 establishes the structural foundation and verifies that:
1. The FastAPI backend serves clean JSON health diagnostics at `/api/health`.
2. The frontend web UI makes real-time client-to-server HTTP calls and renders connection latency and component states.
3. Service interfaces for transcription, Hindsight, and LLM reasoning are registered and ready for Phase 2.
