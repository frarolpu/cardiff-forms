# System Architecture

## Overview

Cardiff Forms is a client-server web application. The browser loads a single HTML page (`index.html`) that communicates with a Python backend over HTTP. The backend generates PDFs and persists data to either a PostgreSQL database or the local filesystem.

```
┌─────────────────────────────────────────────────────────┐
│                       Browser                           │
│                                                         │
│   index.html  (HTML + CSS + Vanilla JS, ~3 300 lines)  │
│       │                                                 │
│       │  fetch() calls                                  │
│       ▼                                                 │
│   forms_final.json (served as a static asset)          │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP (JSON)
                           │
          ┌────────────────▼────────────────┐
          │         Python Backend           │
          │                                 │
          │  Production  →  app.py (Flask)  │
          │  Local dev   →  server.py       │
          └──────┬──────────────┬───────────┘
                 │              │
         ┌───────▼──────┐  ┌───▼──────────┐
         │  PostgreSQL   │  │  Filesystem  │
         │  (DATABASE_   │  │  saved_forms/│
         │   URL env)    │  │  forms/      │
         └───────────────┘  └─────────────┘
```

---

## Technology Stack

### Frontend
| Technology | Role |
|---|---|
| HTML5 | Markup / single-page app shell |
| CSS3 | Styling, responsive layout, print styles |
| Vanilla JavaScript (ES2020) | UI logic, state management, API calls |

No external framework or build step is required. The entire frontend is self-contained in `index.html`.

### Backend
| Technology | Version | Role |
|---|---|---|
| Python | 3.11 | Runtime |
| Flask | 2.3.0 | Production HTTP server / API |
| Gunicorn | 21.2.0 | Production WSGI server |
| fpdf2 | 2.7.1 | PDF generation (app.py) |
| ReportLab | latest | PDF generation (server.py) |
| Pillow | latest | Image processing for PDFs |
| psycopg2-binary | 2.9.9 | PostgreSQL driver |

### Infrastructure
| Service | Role |
|---|---|
| Render | Cloud hosting platform |
| PostgreSQL | Persistent form + PDF storage (production) |
| Docker | Optional containerised deployment |

---

## Directory Structure

```
Cardiff Forms/
│
├── index.html              Main single-page application (frontend)
├── app.py                  Flask production backend (1 020 lines)
├── server.py               Simple HTTP dev server (762 lines)
│
├── forms_final.json        154 maintenance forms (canonical data)
├── forms_parsed.json       Backup of extracted forms
├── forms_with_shading.json Backup with shading metadata
├── extracted_forms.json    Raw extraction output
│
├── saved_forms/            Form archive (JSONs + PDFs)
├── forms/                  Legacy PDF output directory (server.py)
│
├── Dockerfile              Container build instructions
├── docker-compose.yml      Docker Compose config
├── render.yaml             Render cloud deployment config
├── Procfile                Gunicorn start command (legacy Heroku style)
├── requirements.txt        Python dependencies
├── runtime.txt             Python version pin (3.11.8)
│
├── Cardiff-Council-Logo.jpg  Header logo (Cardiff Council)
├── Cardiff_Council.svg       SVG version of the logo
├── SICE-1024x452-1.png       SICE company logo
├── Logos Combined.jpg        Combined logos for PDF header
│
├── docs/                   ← THIS DOCUMENTATION FOLDER
│
└── additional material/    Source DOCX and spreadsheet files
    ├── Section 4 Schedule of Reports Word Nuevo.docx
    └── Sections _ Frequencies.xlsx
```

---

## Two Server Files Explained

### `app.py` — Production Flask Backend

- Used in production on Render (started via Gunicorn)
- Full REST API with all endpoints (see [api-reference.md](api-reference.md))
- Uses `fpdf2` for PDF generation
- Connects to PostgreSQL when `DATABASE_URL` env var is set; falls back to filesystem
- Serves `index.html` and all static assets as well

### `server.py` — Legacy Simple HTTP Server

- Uses Python's built-in `http.server` module — no Flask dependency needed
- Only exposes: `POST /generate-pdf`, `POST /save-pdf`, `POST /save-form`, `GET /list-forms`, `GET /download-form/<name>`
- Uses ReportLab + Pillow for PDF generation
- Useful for offline / air-gapped environments
- Runs on port 5000 by default (overridable via `PORT` env var)

In normal development, prefer starting `app.py` directly or use `gunicorn`.
