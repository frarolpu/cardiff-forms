# API Reference

All endpoints are provided by `app.py` (Flask). The simple `server.py` only implements a subset; those differences are noted.

Base URL (local): `http://localhost:5000`  
Base URL (production): `https://cardiff-forms.onrender.com` (or your Render URL)

---

## Static Assets

### `GET /`
Returns `index.html` — the main single-page application.

### `GET /<path:filename>`
Serves any static file from the working directory (images, JSON files, etc.).

Examples:
- `GET /forms_final.json` — returns the 154-form master JSON array
- `GET /Cardiff_Council.svg` — returns the Cardiff Council logo
- `GET /SICE-1024x452-1.png` — returns the SICE logo

---

## Form Save & Retrieve

### `POST /api/save-form`

Saves a completed or partially-completed form. Generates a PDF and persists it to the database (or filesystem). Also always writes a `.json` file to `saved_forms/` regardless of database availability.

**Request body** (JSON):
```json
{
  "section": "2.1.3",
  "status": "pending_supervisor",
  "equipment": "SWITCHBOARD",
  "inspector": "John Smith",
  "inspectionDate": "2026-03-06",
  "tasks": [{ "step": "1", "description": "...", "completed": true }],
  "engineer_comments": "...",
  "supervisor_comments": "",
  "council_comments": "",
  "materials_used": "...",
  "beforePhotos": ["data:image/jpeg;base64,..."],
  "afterPhotos": [],
  "signatures": {
    "engineer": "John Smith", "engineerInitials": "JS", "engineerDate": "2026-03-06",
    "supervisor": "", "supervisorInitials": "", "supervisorDate": "",
    "council": "", "councilInitials": "", "councilDate": ""
  }
}
```

**Success response** `200`:
```json
{
  "success": true,
  "message": "Form 2.1.3 saved successfully as pending_supervisor",
  "filename": "2.1.3_20260306_142300_PENDING_SUPERVISOR.pdf",
  "status": "pending_supervisor"
}
```

**Error response** `400` / `500`:
```json
{ "success": false, "message": "Error saving form: ..." }
```

---

### `GET /get-saved-forms`

Returns all saved forms (from database or filesystem), ordered newest-first.

**Response** `200`:
```json
{
  "success": true,
  "count": 12,
  "forms": [
    {
      "id": 42,
      "filename": "2.1.3_20260306_142300.pdf",
      "section": "2.1.3",
      "created_at": "2026-03-06T14:23:00",
      "engineer": "John Smith",
      "supervisor": "Ana Suárez",
      "council": "N/A"
    }
  ]
}
```

---

### `GET /api/download-form/<form_identifier>`

Downloads a specific form PDF. `form_identifier` may be:
- A numeric database ID (e.g. `42`)
- A filename stored on disk (e.g. `2.1.3_20260306_142300.pdf`)

**Response**: Binary PDF stream with `Content-Disposition: attachment`.

---

## Pending / Council / Paused Forms

### `GET /api/pending-forms`

Lists all forms in `pending_supervisor` state.

**Response** `200`:
```json
{
  "success": true,
  "count": 3,
  "forms": [
    {
      "id": 15,
      "filename": "2.3.1_20260306_142300_PENDING_SUPERVISOR.pdf",
      "section": "2.3.1",
      "status": "pending_supervisor",
      "created_at": "2026-03-06T14:23:00"
    }
  ]
}
```

---

### `GET /api/council-forms`

Lists all forms in `pending_council` state (same structure as pending-forms response, status is `"pending_council"`).

---

### `GET /api/load-pending-form/<form_id>`

Loads the full form data for a pending form so the supervisor or council can complete it.

`form_id` — numeric DB id, or the filename stem (without status suffix or extension).

**Response** `200`:
```json
{
  "success": true,
  "data": { /* full form JSON as originally submitted */ },
  "filename": "2.3.1_20260306_142300.pdf",
  "status": "pending_supervisor"
}
```

**Response** `404`:
```json
{ "success": false, "message": "Form not found" }
```

---

### `GET /api/paused-forms`

Lists all paused forms (files matching `*_PAUSED_*.json` in `saved_forms/`).

**Response** `200`:
```json
{
  "success": true,
  "count": 1,
  "forms": [
    {
      "id": "2.36.3_20260305_102143",
      "filename": "2.36.3_20260305_102143_PAUSED_3601.json",
      "section": "2.36.3",
      "pin": "3601",
      "status": "paused",
      "created_at": "2026-03-05T10:21:43"
    }
  ]
}
```

---

### `POST /api/pause-form`

Saves a paused form with a 4-digit PIN.

**Request body** (JSON): Full form data plus `"pin": "3601"`.

**Response** `200`:
```json
{
  "success": true,
  "message": "Form paused with PIN: 3601",
  "pin": "3601",
  "filename": "2.36.3_20260305_102143_PAUSED_3601.json"
}
```

---

### `GET /api/resume-paused-form/<pin>`

Loads a paused form by its 4-digit PIN.

**Response** `200`:
```json
{
  "success": true,
  "data": { /* full form JSON */ },
  "filename": "2.36.3_20260305_102143.pdf",
  "status": "paused"
}
```

**Response** `404`:
```json
{ "success": false, "message": "Paused form not found with this PIN" }
```

---

## Legacy (server.py only)

These endpoints exist only in the simple HTTP dev server (`server.py`):

| Method | Path | Description |
|--------|------|-------------|
| POST | `/generate-pdf` | Generate PDF from form JSON, save to `forms/` |
| POST | `/save-pdf` | Save raw PDF bytes to `forms/` (filename from `X-Filename` header) |
| POST | `/save-form` | Save form JSON to `forms/` (DB + JSON) |
| GET | `/list-forms` | List all PDFs in `forms/` |
| GET | `/download-form/<filename>` | Download a specific PDF from `forms/` |
| GET | `/forms-viewer` | Simple HTML page listing all generated PDFs |

---

## Error Handling

All API endpoints return JSON error bodies. The Flask app has a global exception handler:

```json
{
  "success": false,
  "message": "Server error: <description>",
  "error_type": "ExceptionClassName"
}
```

Unhandled errors are appended to `pdf_errors.log` in the working directory.
