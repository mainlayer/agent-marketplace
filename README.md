# Agent Marketplace

A production-ready marketplace for AI agents with per-call billing powered by
[Mainlayer](https://mainlayer.fr) — payment infrastructure for AI agents.

Developers publish agents as billable resources. Users browse the marketplace,
pay per call, and get results immediately. Every transaction flows through
Mainlayer with no subscription management, no custom billing code, and no
financial risk for publishers.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (React/Vite)               │
│  Marketplace  ──  AgentDetail  ──  Publish               │
│       ↓                ↓              ↓                  │
│               /api/v1 (HTTP)                             │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   Backend (FastAPI)                      │
│                                                          │
│  /agents       Register agents as Mainlayer resources    │
│  /payments     Charge callers, grant entitlements        │
│  /marketplace  Search, filter, discover agents           │
│                                                          │
│                         │                               │
└─────────────────────────┼───────────────────────────────┘
                          │ HTTPS
┌─────────────────────────▼───────────────────────────────┐
│              Mainlayer API (api.mainlayer.fr)           │
│                                                          │
│  Resources     Agents registered as billable resources   │
│  Payments      Per-call charges against payer balances   │
│  Entitlements  Access control after payment              │
└─────────────────────────────────────────────────────────┘
```

### Backend routes

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/agents` | Publish a new agent |
| `GET` | `/api/v1/agents` | List all agents (paginated) |
| `GET` | `/api/v1/agents/{id}` | Agent details |
| `POST` | `/api/v1/payments/agents/{id}/run` | Pay and run agent |
| `GET` | `/api/v1/payments/agents/{id}/entitlement` | Check entitlement |
| `POST` | `/api/v1/payments/agents/{id}/entitlement` | Grant entitlement |
| `GET` | `/api/v1/marketplace/discover` | Browse / search agents |
| `GET` | `/api/v1/marketplace/stats` | Marketplace statistics |
| `GET` | `/api/v1/marketplace/categories` | Available categories |

---

## Prerequisites

- Python 3.12+
- Node 20+
- A Mainlayer API key from [mainlayer.fr](https://mainlayer.fr)

---

## Quickstart (local)

### 1. Backend

```bash
cd backend
cp .env.example .env
# Edit .env and add your MAINLAYER_API_KEY

pip install -r requirements.txt
uvicorn backend.main:app --reload
# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# UI available at http://localhost:5173
```

---

## Docker Compose

```bash
cp backend/.env.example backend/.env
# Edit backend/.env — set MAINLAYER_API_KEY

docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

## Publishing an agent

### Via the UI

1. Open the marketplace and click **Publish Agent**.
2. Fill in the name, description, category, price per call, and capabilities.
3. Click **Publish Agent** — your agent is instantly live and billable.

### Via the API

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smart Summarizer",
    "description": "Summarizes any text in under 100 words.",
    "category": "NLP",
    "price_per_call": 0.02,
    "capabilities": [
      {"name": "Text Summarization", "description": "Condenses long text."}
    ],
    "tags": ["summarization", "nlp", "productivity"],
    "example_input": "{\"text\": \"Long article here...\"}",
    "example_output": "Three-sentence summary."
  }'
```

---

## Running an agent (paying per call)

```bash
curl -X POST http://localhost:8000/api/v1/payments/agents/{AGENT_ID}/run \
  -H "Content-Type: application/json" \
  -d '{
    "payer_api_key": "ml_live_your_key_here",
    "input_data": {"text": "Summarize this for me."}
  }'
```

Mainlayer charges `price_per_call` from the payer's balance and returns the
agent output in the same response.

---

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MAINLAYER_API_KEY` | Yes | — | Publisher's Mainlayer API key |
| `MAINLAYER_BASE_URL` | No | `https://api.mainlayer.fr` | Override API base URL |
| `HOST` | No | `0.0.0.0` | Uvicorn bind host |
| `PORT` | No | `8000` | Uvicorn bind port |

Frontend:

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000/api/v1` | Backend API base URL |

---

## Project structure

```
agent-marketplace/
├── backend/
│   ├── main.py            # FastAPI app entry point
│   ├── mainlayer.py       # Mainlayer API client
│   ├── models.py          # Pydantic request/response models
│   ├── store.py           # In-memory agent registry
│   ├── routes/
│   │   ├── agents.py      # Agent registration and retrieval
│   │   ├── payments.py    # Pay-to-run and entitlement routes
│   │   └── marketplace.py # Discovery, search, stats
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Root with routing and nav
│   │   ├── main.tsx            # React entry point
│   │   ├── api/mainlayer.ts    # Typed API client
│   │   ├── components/
│   │   │   └── AgentCard.tsx   # Marketplace card component
│   │   └── pages/
│   │       ├── Marketplace.tsx # Browse / search page
│   │       ├── AgentDetail.tsx # Agent page + Pay & Run
│   │       └── Publish.tsx     # Publish form
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── Dockerfile
│   ├── nginx.conf
│   └── index.html
├── .github/workflows/ci.yml
└── docker-compose.yml
```

---

## Production considerations

- **Database**: Replace `backend/store.py` (in-memory dict) with Postgres or
  another persistent store.
- **Agent execution**: Replace the stub `_execute_agent` function in
  `routes/payments.py` with real inference calls to your AI backend.
- **Auth**: Add API key validation middleware to protect admin routes.
- **CORS**: Lock down `allow_origins` in `main.py` to your production domain.
- **Secrets**: Use a secrets manager (AWS Secrets Manager, Vault, etc.) instead
  of `.env` files in production.
