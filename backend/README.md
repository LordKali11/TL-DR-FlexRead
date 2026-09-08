# NZZ FlexRead Backend (Stream 2: Data & Content Personalisation)

Backend implementation for **NZZ FlexRead**, designed for high-throughput, low-latency adaptive content delivery powered by FastAPI, Google Gemini / Vertex AI, multi-tier caching (Redis/SQLite/In-Memory), and Google AntiGravity agentic workflows.

---

## 🎯 Objectives & Architecture

- **Target Audience:** Busy professionals, commuters, and social media traffic (~800,000 annual social clicks with ~90% bounce rate) who demand adaptive reading lengths without sacrificing depth.
- **Core Solution:** Dynamically transforms text-dense NZZ articles into scalable reading modes (**60-second essentials**, **structured key bullet points**, **simplified inline passages**, and **full deep-dives**) while maintaining NZZ's distinct analytical and sober editorial voice.
- **Standardized Output Contract:**
  Every transformed variant guarantees the triple:
  ```json
  {
    "title": "Adapted headline",
    "summary": "Executive lead / summary",
    "actual_content": "Markdown-formatted transformed body"
  }
  ```

---

## 🛠 Tech Stack

- **Framework:** FastAPI (Python 3.12+ / 3.14)
- **AI / LLM:** Google Gemini API (`gemini-2.5-flash`), Vertex AI, Google AntiGravity Agentic Integration
- **Caching Layer:** Redis & SQLite / In-Memory multi-tier cache
- **Deployment Target:** GCP Cloud Run (Containerized via Docker)

---

## 📂 Project Structure

```
backend/
├── app/
│   ├── config.py                 # Pydantic Settings & environment variables
│   ├── main.py                   # FastAPI application & startup lifecycle
│   ├── models/
│   │   ├── article.py            # Article, Preprocessing, ReadingMode, FlexReadVariant
│   │   ├── user.py               # UserProfile, UserPreferences, ReadingHistory
│   │   └── api.py                # Request and Response schemas
│   ├── services/
│   │   ├── article_ingestion.py  # Ingestion scanner for input/days and input/longform
│   │   ├── preprocessor.py       # Preprocessing: main points, keywords, tone, length tier, reading time, word count
│   │   ├── prompt_engine.py      # Structured system prompts for AntiGravity / Gemini
│   │   ├── gemini_client.py      # Google GenAI client with deterministic editorial fallback
│   │   ├── cache_service.py      # Multi-tier caching across all reading lengths
│   │   └── user_service.py       # User management, stats, and commute time personalization
│   └── routers/
│       ├── articles.py           # Ingest, list, retrieve, and generate reading modes
│       ├── users.py              # User profiles, reading history, and stats
│       ├── personalization.py    # Adaptive commute feeds & mode recommendations
│       └── system.py             # Health check & cache statistics
├── tests/                        # Pytest unit and integration test suite
├── Dockerfile                    # Production GCP Cloud Run container
├── run.sh                        # Local execution script
└── requirements.txt              # Production dependencies
```

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
uv venv backend/.venv
source backend/.venv/bin/activate
uv pip install -r backend/requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp backend/.env.example backend/.env
```
Add your `GEMINI_API_KEY` (optional; an offline NZZ editorial generator is included for offline development and CI).

### 3. Run Backend
```bash
./backend/run.sh
# Server starts at http://localhost:8000
# Interactive Swagger UI: http://localhost:8000/docs
```

### 4. Run Tests
```bash
PYTHONPATH=. backend/.venv/bin/pytest backend/tests -v
```

---

## 🔌 API Endpoints Summary

### 1. Articles & FlexRead Modes
- `POST /api/articles/ingest?force_reload=false` — Scans `input/` folder and indexes all articles.
- `GET /api/articles?section=Wirtschaft&limit=20` — Lists indexed articles with preprocessing metadata.
- `GET /api/articles/{article_id}` — Gets article detail with full preprocessing phase results (`main_points`, `keywords`, `tone`, `article_length`, `reading_time`, `word_count`).
- `GET /api/articles/{article_id}/read?mode={mode}&user_id={user_id}` — Returns transformed variant (`title`, `summary`, `actual_content`) for modes:
  - `60s` (60-second essentials)
  - `bullet_points` (Key structured takeaways)
  - `inline_simplified` (Simplified inline passages for commuters / social clicks)
  - `full` (Original deep-dive)

### 2. User Management & Personalization
- `POST /api/users` — Creates user profile with reading speed (WPM) and commute time budget.
- `GET /api/users/{user_id}` — Gets user profile.
- `PUT /api/users/{user_id}/preferences` — Updates reading preferences.
- `POST /api/users/{user_id}/history` — Logs reading events.
- `GET /api/users/{user_id}/stats` — Calculates total reading time and estimated time saved.
- `GET /api/personalize/{user_id}/feed?time_budget_minutes=3` — Dynamically suggests optimal reading modes fitting the user's commute time window.

### 3. Cache & System
- `GET /health` — Service health check.
- `GET /api/cache/stats` — Reports cache hits, misses, and stored variants count.
- `POST /api/cache/clear` — Clears cache.

---

## ☁️ Google Cloud Platform (GCP) Deployment

The backend is cloud-native and designed for **GCP Cloud Run** with **Vertex AI**:

### 1-Click Automated Deployment
```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud config set project YOUR_GCP_PROJECT_ID

# Run the deployment script
./deploy_gcp.sh
```

### Cloud Run Architecture Highlights
1. **Container Port:** Dynamically listens on `0.0.0.0:${PORT}` (Cloud Run default: 8080).
2. **Vertex AI Native:** Seamlessly leverages GCP Service Account Application Default Credentials (ADC) for Gemini models (`gemini-2.5-flash`), eliminating hardcoded API keys.
3. **Stateless Autoscaling:** Cold start < 2 seconds, scales to zero when idle, multi-tier persistent caching.
4. **CI/CD Integration:** Ready for Cloud Build via [`cloudbuild.yaml`](../cloudbuild.yaml).

