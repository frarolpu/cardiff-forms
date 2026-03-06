# Deployment Guide

## Prerequisites

- Python 3.11
- pip
- (optional) PostgreSQL instance for production storage
- (optional) Docker + Docker Compose for containerised dev

---

## Option 1 — Local Development (Flask, recommended)

```powershell
cd "c:\TempApp\Cardiff Forms"

# Create and activate virtual environment (first time only)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies (first time only)
pip install -r requirements.txt

# Run the Flask app
python app.py
```

Open `http://localhost:5000` in your browser.

**Environment variables** (optional, create a `.env` file or set in shell):

```env
PORT=5000
DATABASE_URL=postgresql://user:pass@host:5432/dbname
ENVIRONMENT=development
```

If `DATABASE_URL` is not set, the app stores data in `saved_forms/` on disk.

---

## Option 2 — Local Development (simple HTTP server)

This requires no Flask. Uses Python's built-in `http.server`:

```powershell
python server.py
```

Open `http://localhost:5000`. This server has limited API endpoints (no PDF-in-database, no pending-forms workflow). Use only for quick form viewing.

---

## Option 3 — Docker

```powershell
# Build and start
docker compose up --build

# Stop
docker compose down
```

The `Dockerfile` copies all files, installs requirements, and runs `python app.py` on port 5000.

`docker-compose.yml` exposes port 5000 on the host. Configure a `DATABASE_URL` environment variable in the compose file for database persistence.

---

## Option 4 — Production on Render

The project is configured for [Render](https://render.com) via `render.yaml`.

**Render service config** (`render.yaml`):
```yaml
services:
  - type: web
    name: cardiff-forms
    runtime: python
    startCommand: gunicorn --workers 4 --bind 0.0.0.0:$PORT --timeout 120 app:app
    buildCommand: pip install -r requirements.txt
    env:
      - key: PYTHON_VERSION
        value: "3.11"
```

**Steps to deploy**:
1. Push the repository to GitHub / GitLab
2. Create a new **Web Service** on Render, linking the repo
3. Render auto-detects `render.yaml` and uses the above config
4. Set the `DATABASE_URL` environment variable in the Render dashboard (from your PostgreSQL add-on)
5. Render will run the build command, then start the app

**Procfile** (legacy Heroku format, also present):
```
web: gunicorn --workers 4 --bind 0.0.0.0:$PORT --timeout 120 app:app
```

---

## Keep-Alive (Render Free Tier)

Render free-tier services spin down after 15 minutes of inactivity. The project includes utilities to prevent this:

| File | Description |
|------|-------------|
| `keep_render_alive.py` | Python script that pings the site every 10 minutes |
| `keep-render-alive.ps1` | PowerShell version of the same |
| `run-keep-alive.bat` | Windows batch launcher for `keep-render-alive.ps1` |
| `KEEP-ALIVE-SETUP.md` | Instructions for scheduling the keep-alive script |

Run `python keep_render_alive.py` on any machine that stays awake to keep the Render instance warm.

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5000` | Port to listen on |
| `DATABASE_URL` | (none) | PostgreSQL connection string — if absent, filesystem is used |
| `ENVIRONMENT` | (none) | Set to `production` to disable Flask debug mode |

---

## Directory Permissions

On first run, the app creates:
- `saved_forms/` — JSON and PDF archives
- `forms/` — legacy PDF output for `server.py`

Both directories must be writable by the process user. On Render, the working directory is writable by default.

---

## Python Version

The project pins Python 3.11.8 via `runtime.txt`. This is used by Render and Heroku-style platforms.

---

## Dependencies (`requirements.txt`)

```
fpdf2==2.7.1
psycopg2-binary==2.9.9
python-dotenv==1.0.0
Flask==2.3.0
gunicorn==21.2.0
```

`server.py` additionally uses `reportlab` and `Pillow`, which must be installed separately if you use that server. They are not in `requirements.txt`.

---

## Logs

| File | Content |
|------|---------|
| `pdf_errors.log` | Timestamped errors from `app.py` (PDF gen, DB, file I/O) |
| `flask_debug.log` | Flask debug output (if redirected) |
| `flask_output.log` | Flask stdout output (if redirected) |
