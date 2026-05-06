# Savings Yield Optimiser

Local-first UK savings + Cash ISA rate tracker.

## Prereqs
- Python (3.11+ recommended)
- Node.js (18+)

## Setup
### Python (root venv)
```bash
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Initialise local SQLite DB
```bash
.\.venv\Scripts\python -m backend.app.cli.init_db
```

### Seed sample data
```bash
.\.venv\Scripts\python -m backend.app.cli.seed_db
```

### Run API (local)
```bash
.\.venv\Scripts\python -m uvicorn backend.app.main:app --reload
```

