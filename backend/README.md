# NZZ FlexRead Backend (Stream 2: Data & Content Personalisation)

Backend implementation for **NZZ FlexRead**, designed for high-throughput, low-latency adaptive content delivery powered by FastAPI, MongoDB (primary persistent database), Redis (ultra-fast cache layer), Google Gemini / Vertex AI, and Google AntiGravity agentic workflows.

---

## 🎯 Objectives & Architecture

- **Target Audience:** Busy professionals, commuters, and social media traffic (~800,000 annual social clicks with ~90% bounce rate) who demand adaptive reading lengths without sacrificing depth.
- **Language Focus:** **English ONLY** (focusing on global professional commuters and international traffic).
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
- **Database & Cache Architecture:**
  - **Primary Persistent Database:** **MongoDB** (stores raw articles, enriched editorial metadata, and user profiles).
  - **Ultra-Fast Cache Layer:** **Redis** (caches pre-processed article metadata, feed queries, and pre-warmed reading mode variants for sub-10ms delivery).
  - **Pre-processing Service:** Ingests raw data from MongoDB, executes the editorial preprocessing phase (`main_points`, `keywords`, `tone`, `article_length`, `reading_time`, `word_count`), updates MongoDB as the system of record, and populates Redis.

---

## 🛠 Tech Stack

- **Framework:** FastAPI (Python 3.12+ / 3.14)
- **Primary Database:** MongoDB (`pymongo`, `motor`, with `mongomock` fallback for local/offline resilience)
- **Ultra-Fast Cache:** Redis (`redis-py`)
- **AI / LLM:** Google Gemini API (`gemini-2.5-flash`), Vertex AI, Google AntiGravity Agentic Integration
- **Deployment Target:** GCP Cloud Run (Containerized via Docker)

---

## 📂 Project Structure

```
backend/
├── app/
│   ├── config.py                     # MongoDB, Redis, GCP, and App settings
│   ├── main.py                       # FastAPI application & startup lifecycle
│   ├── db/
│   │   ├── __init__.py
│   │   └── mongodb.py                # MongoDB persistent database manager & fail-safe mock
│   ├── models/
│   │   ├── article.py                # Article, Preprocessing, ReadingMode, FlexReadVariant
│   │   ├── user.py                   # UserProfile, UserPreferences, ReadingHistory
│   │   └── api.py                    # Request and Response schemas
│   ├── services/
│   │   ├── article_ingestion.py      # Scans input folders -> stores to MongoDB
│   │   ├── preprocessor.py           # Preprocessing: main points, keywords, tone, length tier, reading time, word count
│   │   ├── preprocessing_service.py  # Ingests from MongoDB -> applies preprocessing -> populates Redis
│   │   ├── prompt_engine.py          # English system prompts for AntiGravity / Gemini
│   │   ├── gemini_client.py          # Vertex AI & Gemini client with English offline fallback
│   │   ├── cache_service.py          # Ultra-fast Redis cache layer across reading lengths
│   │   └── user_service.py           # User management persisted in MongoDB & cached in Redis
│   └── routers/
│       ├── articles.py               # Ingest, list, retrieve, preprocess, and generate reading modes
│       ├── users.py                  # User profiles, reading history, and stats
│       ├── personalization.py        # Adaptive commute feeds & mode recommendations
│       └── system.py                 # Health check (reporting MongoDB & Redis status) & cache stats
├── tests/                            # Pytest unit and integration test suite (19 passing tests)
├── Dockerfile                        # Production GCP Cloud Run container
├── run.sh                            # Local execution script
└── requirements.txt                  # Production dependencies
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
Key settings:
- `MONGODB_URI=mongodb://localhost:27017`
- `MONGODB_DB_NAME=nzz_flexread`
- `REDIS_URL=redis://localhost:6379/0`
- `GEMINI_API_KEY=your_gemini_api_key_here` (optional; English fallback generator included)

### 3. Run Backend
```bash
./backend/run.sh
# Server starts at http://localhost:8080
# Interactive Swagger UI: http://localhost:8080/docs
```

### 4. Run Tests
```bash
PYTHONPATH=. backend/.venv/bin/pytest backend/tests -v
```

---

## 🔌 API Endpoints Summary

### 1. Articles & Pre-processing Pipeline
- `POST /api/articles/ingest?force_reload=false` — Ingests articles from `input/` folder directly into MongoDB and populates Redis.
- `POST /api/articles/{article_id}/preprocess?warm_variants=true` — Ingests article from MongoDB, applies pre-processing logic, writes back to MongoDB, and populates Redis cache.
- `POST /api/articles/preprocess/batch?limit=50&warm_variants=false` — Batch-processes unprocessed articles from MongoDB into Redis.
- `GET /api/articles?section=Business&limit=20` — Lists articles with preprocessed metadata.
- `GET /api/articles/{article_id}` — Gets full article with `main_points`, `keywords`, `tone`, `article_length`, `reading_time`, and `word_count`.
- `GET /api/articles/{article_id}/read?mode={mode}&user_id={user_id}` — Returns transformed variant (`title`, `summary`, `actual_content`) served from Redis in sub-milliseconds:
  - `60s` (60-second essentials)
  - `bullet_points` (Executive briefing bullets)
  - `inline_simplified` (Simplified narrative with inline explanations)
  - `full` (Original deep-dive)

### 2. Personalization & Commuter Transit Budget
- `GET /api/personalize/{user_id}/feed?time_budget_minutes=3` — Dynamically selects articles and best reading modes fitting the commuter's exact travel window.

### 3. User Management
- `POST /api/users` — Creates user profile in MongoDB.
- `GET /api/users/{user_id}` — Fetches user profile.
- `GET /api/users/{user_id}/stats` — Returns reading analytics and estimated time saved.

### 4. System & Health
- `GET /health` — Returns service health, Gemini status, MongoDB status, and Redis status.
- `GET /api/cache/stats` — Reports Redis hit/miss rates and key count.
