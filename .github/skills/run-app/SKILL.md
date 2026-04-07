---
name: run-app
description: "Run the full Todo application (backend + frontend). Use when: starting the dev environment, launching the API and UI together, setting up for local development, running the FastAPI backend or the React Vite frontend, starting the app from scratch."
argument-hint: "Optional: 'backend', 'frontend', or 'all' (default: all)"
---

# Run Full Application (Backend + Frontend)

Starts the FastAPI backend and React/Vite frontend for local development.

## Prerequisites

- **SQL Server** running on `localhost:1433` with database `todo_db`
- **Python** (3.11+) with a virtual environment in `api/`
- **Node.js** (18+) and npm

## Procedure

### 1. Verify / Create Environment Files

Check both `.env` files exist. If missing, copy from the examples:

```powershell
# Backend
if (!(Test-Path api/.env)) { Copy-Item api/.env.example api/.env }

# Frontend
if (!(Test-Path web/.env)) { Copy-Item web/.env.example web/.env }
```

> Edit `api/.env` to confirm `DB_HOST` and `DB_NAME` match your SQL Server instance.

### 2. Run Database Migrations

Ensure the schema is current before starting the API:

```powershell
cd api
alembic upgrade head
cd ..
```

### 3. Start the Backend (FastAPI)

Open a terminal, activate the virtual environment, and launch Uvicorn:

```powershell
cd api
.\.venv\Scripts\Activate.ps1   # Windows — adjust path if venv is elsewhere
uvicorn app.main:app --reload
```

- Runs on **http://localhost:8000**
- Interactive docs: **http://localhost:8000/docs**
- Health check: **http://localhost:8000/health**

### 4. Start the Frontend (React/Vite)

Open a **second terminal** and start Vite:

```powershell
cd web
npm install       # only needed on first run or after dependency changes
npm run dev
```

- Runs on **http://localhost:5173**
- Vite proxies `/api/*` → `http://localhost:8000` automatically

## Verification Checklist

- [ ] `http://localhost:8000/health` returns `{"status": "ok"}`
- [ ] `http://localhost:5173` loads the Todo UI without errors
- [ ] Browser DevTools Network tab shows API calls returning 2xx

## Stopping the App

Press `Ctrl+C` in each terminal window.

## Common Issues

| Symptom | Fix |
|---------|-----|
| `uvicorn: command not found` | Activate the virtual environment first |
| `ODBC Driver not found` | Install **ODBC Driver 17 for SQL Server** |
| `Connection refused` on port 1433 | Start SQL Server service |
| `alembic: command not found` | Activate the virtual environment first |
| Blank frontend with API errors | Check `CORS_ORIGINS` in `api/.env` includes `http://localhost:5173` |
| `npm: command not found` | Install Node.js 18+ |
