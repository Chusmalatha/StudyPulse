# StudyPulse.AI — Autonomous AI Study & Knowledge Companion

> **GitHub Repository Description (Short):**
> *An autonomous AI-powered study companion featuring grounded RAG tutoring, PDF document processing, adaptive practice quizzes, concept mastery tracking, and learning analytics.*

> **Repository Topics/Tags:** `ai-study-companion` `rag-tutor` `fastapi` `react` `mongodb` `groq-llm` `vector-search` `adaptive-learning` `tailwind-css` `pydantic`

---

StudyPulse.AI is an intelligent, full-stack AI study platform designed to transform static study materials into active retention. It provides document-grounded AI tutoring, automated vector RAG search, adaptive quizzes, concept mastery analytics, and executive admin monitoring.

##### Current Implementation Status: Phase 11 — Security + Reliability + AI Observability + Testing

Phase 0 established architecture, Phase 1 implemented authentication, Phase 2 implemented Spaces & Projects, Phase 3 implemented PDF upload & background processing, Phase 4 delivered Knowledge Extraction & RAG Search, Phase 5 implemented AI Tutor, Phase 6 delivered Adaptive Quizzes & Assessment, Phase 7 delivered Concept Mastery & Persistent Context, Phase 8 implemented Growth Analysis + Recommendations, Phase 9 delivered Events + Background Learning Workflows, Phase 10 delivered Analytics + Admin Dashboard, and Phase 11 delivers **Security + Reliability + AI Observability + Testing** — featuring strict project isolation server-side validation, PDF path traversal & MIME validation, AI Tutor prompt-injection boundaries, structured `AIUsage` execution logging, deterministic `AIEvaluation` checks (grounding, citations, quiz structure), background worker retry limits, and automated unit/integration test suites.

## Technology Stack

* **Frontend**: React.js 19, Vite, Tailwind CSS, React Router, Axios
* **Backend**: Python 3.10, FastAPI, Motor (async MongoDB), Pydantic v2
* **Database**: MongoDB (Atlas or local)
* **Auth**: JWT (python-jose) + bcrypt password hashing

---

## Local Setup

### 1. Environment Variables

**Backend:**
```bash
cd backend
cp .env.example .env
# Fill in your values — especially MONGODB_URI and JWT_SECRET
```

**Frontend:**
```bash
cd frontend
cp .env.example .env
# VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 2. Backend Setup

Prerequisites: Python 3.10+, MongoDB running locally or Atlas URI.

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate        # Windows
source venv/bin/activate        # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

**Run the backend:**
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### 3. Frontend Setup

Prerequisites: Node.js 18+.

```bash
cd frontend
npm install
```

**Run the frontend:**
```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

---

## Authentication Flow

```
Register  →  POST /api/v1/auth/register  →  User created in MongoDB
Login     →  POST /api/v1/auth/login     →  JWT access token returned
Dashboard →  GET  /api/v1/auth/me        →  Current user loaded from JWT
Logout    →  Client removes token        →  Redirect to /login
```

## Available API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/register` | Create a new user account | No |
| POST | `/api/v1/auth/login` | Login and receive JWT token | No |
| GET | `/api/v1/auth/me` | Get current authenticated user | Yes (Bearer) |
| GET | `/api/v1/health` | Backend health check | No |
| POST | `/api/v1/spaces` | Create Space | Yes (Bearer) |
| GET | `/api/v1/spaces` | List authenticated user's Spaces | Yes (Bearer) |
| POST | `/api/v1/projects/{project_id}/materials` | Upload PDF Material & queue processing | Yes (Bearer) |
| GET | `/api/v1/projects/{project_id}/materials` | List Materials for Project | Yes (Bearer) |
| GET | `/api/v1/materials/{material_id}` | Get single Material status | Yes (Bearer) |
| POST | `/api/v1/materials/{material_id}/retry` | Retry background processing for failed Material | Yes (Bearer) |
| GET | `/api/v1/materials/{material_id}/chunks` | Get processed Chunks with `page_number` metadata | Yes (Bearer) |
| DELETE | `/api/v1/materials/{material_id}` | Delete Material, file, chunks, and job tracking | Yes (Bearer) |
| POST | `/api/v1/projects/{project_id}/search` | Perform semantic vector RAG search inside project knowledge | Yes (Bearer) |
| GET | `/api/v1/projects/{project_id}/knowledge` | Get extracted Concepts, Topics, and Sections for a project | Yes (Bearer) |
| POST | `/api/v1/projects/{project_id}/knowledge/extract` | Manually trigger/refresh knowledge extraction | Yes (Bearer) |
| POST | `/api/v1/projects/{project_id}/tutor/conversations` | Create a new AI Tutor conversation | Yes (Bearer) |
| GET | `/api/v1/projects/{project_id}/tutor/conversations` | List AI Tutor conversations for a project | Yes (Bearer) |
| GET | `/api/v1/projects/{project_id}/tutor/conversations/{conversation_id}` | Get conversation metadata | Yes (Bearer) |
| GET | `/api/v1/projects/{project_id}/tutor/conversations/{conversation_id}/messages` | List conversation messages | Yes (Bearer) |
| POST | `/api/v1/projects/{project_id}/tutor/conversations/{conversation_id}/messages` | Send question & receive grounded answer with citations | Yes (Bearer) |
| POST | `/api/v1/projects/{project_id}/assessments` | Create a new adaptive practice assessment | Yes (Bearer) |
| GET | `/api/v1/projects/{project_id}/assessments` | List past assessments for a project | Yes (Bearer) |
| GET | `/api/v1/projects/{project_id}/assessments/{assessment_id}` | Get assessment details and questions | Yes (Bearer) |
| POST | `/api/v1/projects/{project_id}/assessments/{assessment_id}/questions/{question_id}/answer` | Submit answer for MCQ or Open-ended question | Yes (Bearer) |
| POST | `/api/v1/projects/{project_id}/assessments/{assessment_id}/complete` | Complete assessment and calculate score | Yes (Bearer) |
| GET | `/api/v1/projects/{project_id}/mastery` | Get concept mastery summary & overall score | Yes (Bearer) |
| GET | `/api/v1/projects/{project_id}/mastery/{concept_id}` | Get detailed concept mastery breakdown with audit logs & mistakes | Yes (Bearer) |
| GET | `/api/v1/projects/{project_id}/growth` | Get concept growth trajectories and summary | Yes (Bearer) |
| GET | `/api/v1/projects/{project_id}/recommendations` | List material-grounded study recommendations | Yes (Bearer) |
| POST | `/api/v1/projects/{project_id}/recommendations/generate` | Generate/refresh study recommendations | Yes (Bearer) |
| POST | `/api/v1/projects/{project_id}/recommendations/{recommendation_id}/complete` | Mark recommendation as completed | Yes (Bearer) |
| POST | `/api/v1/projects/{project_id}/recommendations/{recommendation_id}/dismiss` | Dismiss recommendation | Yes (Bearer) |
| GET | `/api/v1/projects/{project_id}/events` | List activity events stream for a project | Yes (Bearer) |
| GET | `/api/v1/projects/{project_id}/events/{event_id}` | Get single activity event details | Yes (Bearer) |
| GET | `/api/v1/admin/overview` | Platform KPI overview | Yes (Admin Bearer) |
| GET | `/api/v1/admin/ai-usage` | Instrument AI operation metrics and latency | Yes (Admin Bearer) |

## Required Environment Variables

### Backend (`.env`)

| Variable | Description |
|----------|-------------|
| `MONGODB_URI` | MongoDB connection string |
| `MONGODB_DATABASE` | Database name (`ai_study_companion`) |
| `JWT_SECRET` | Secret key for signing JWTs (keep long + random) |
| `JWT_ALGORITHM` | JWT algorithm (`HS256`) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry in minutes (`60`) |
| `FRONTEND_URL` | Frontend URL for CORS |
| `MAX_PDF_SIZE_MB` | Maximum PDF upload size in megabytes (`25`) |
| `EMBEDDING_PROVIDER` | Embedding provider (`local`, `deterministic`) |
| `EMBEDDING_MODEL` | Embedding model identifier (`prototype-64d`) |
| `STORAGE_DIR` | PDF file disk storage directory (`storage/materials`) |
| `GROQ_API_KEY` | Groq Cloud API key for LLM execution |
| `LLM_PROVIDER` | LLM Provider (`groq`, `openai`, or fallback mock) |
| `LLM_MODEL` | LLM Model name (`llama-3.3-70b-versatile`) |
| `TUTOR_RETRIEVAL_TOP_K` | Number of RAG chunks retrieved per tutor question (`5`) |
| `TUTOR_RETRIEVAL_THRESHOLD` | Minimum relevance threshold for grounded RAG (`0.35`) |
| `QUIZ_DEFAULT_QUESTION_COUNT` | Default number of questions generated per assessment (`5`) |

### Frontend (`.env`)

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | Backend API base URL (`http://localhost:8000/api/v1`) |

---

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```



