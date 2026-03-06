# Data Model

## forms_final.json — Master Form Definitions

This is the canonical source of truth for all 154 maintenance forms. It is a JSON array loaded by the frontend at startup.

### Form Object Schema

```jsonc
{
  "section": "2.1.3",          // Unique section identifier (string)
  "equipment": "SWITCHBOARD",  // Equipment / system name
  "drawing_ref": "B8/1 to B8/6", // Drawing reference number(s)
  "locations": [               // Array of location strings
    "SERVICE BUILDING"
  ],
  "frequencies": [             // Inspection frequency labels
    "6 MONTHLY"
  ],
  "tasks": [                   // Ordered list of maintenance tasks
    {
      "step": "1",             // Step number (string)
      "description": "Inspect switchgear for cleanliness"
    }
  ],
  // Optional fields for matrix forms:
  "is_matrix": true,           // Present when form has a selector
  "selector_type": "EDP",      // "EDP" | "EP" | "VP" | "FAN ID" | "Sign"
  "selector_items": ["EDP-01", "EDP-02", ...] // Items in the dropdown
}
```

### Form Counts by Type

| Type | Count | Selector values |
|------|-------|-----------------|
| Regular (no selector) | 111 | — |
| EDP matrix | 28 | 14 items each |
| EP matrix | 4 | 14 items each |
| VP matrix | 4 | 10 items each |
| FAN ID matrix | 4 | 32 items |
| Sign matrix | 1 | 46 sign locations |
| Cross Bore Door | 6 | 7 doors (2.24.1–2.24.6) |
| **Total** | **154** | |

---

## Submitted Form Data (in-flight / saved JSON)

When a user fills out and saves a form, the following JSON object is sent to `POST /api/save-form` and also written as a `.json` file in `saved_forms/`.

```jsonc
{
  // Identity
  "section": "2.6.1",
  "status": "pending_supervisor",  // "new" | "pending_supervisor" | "pending_council" | "complete"

  // General Info
  "equipment": "Fan Unit",
  "drawing_ref": "B8/1",
  "inspector": "John Smith",
  "inspectionDate": "2026-03-06",
  "edp": "EDP-03",              // Only on matrix forms

  // Metadata
  "locations": ["MAIN TUNNEL"],
  "frequencies": ["MONTHLY"],

  // Tasks (each task from the template, plus completion state)
  "tasks": [
    {
      "step": "1",
      "description": "Check fan blades for damage",
      "completed": true
    }
  ],

  // Comments (per role)
  "engineer_comments": "All clear",
  "supervisor_comments": "",
  "council_comments": "",
  "materials_used": "Cleaning rags",

  // Photos (base64 data URIs)
  "beforePhotos": ["data:image/jpeg;base64,..."],
  "afterPhotos":  ["data:image/jpeg;base64,..."],

  // Signatures (three roles)
  "signatures": {
    "engineer":          "John Smith",
    "engineerInitials":  "JS",
    "engineerDate":      "2026-03-06",
    "supervisor":        "",
    "supervisorInitials":"",
    "supervisorDate":    "",
    "council":           "",
    "councilInitials":   "",
    "councilDate":       ""
  },

  // Paused form only
  "pin": "3842"
}
```

---

## Database Schema (PostgreSQL)

```sql
CREATE TABLE IF NOT EXISTS saved_forms (
    id          SERIAL PRIMARY KEY,
    section     VARCHAR(50),
    filename    VARCHAR(255),
    status      VARCHAR(20) DEFAULT 'complete',
    pdf_data    BYTEA,
    form_data   JSONB,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

| Column | Notes |
|--------|-------|
| `status` | `'pending_supervisor'` / `'pending_council'` / `'complete'` |
| `pdf_data` | Full PDF binary stored as bytes |
| `form_data` | Full submitted JSON (used to restore the form for supervisor/council) |

When no `DATABASE_URL` env var is found, the app falls back silently to writing files on the filesystem in `saved_forms/`.

---

## File Naming Convention

Files in `saved_forms/` follow a deterministic naming pattern:

```
{section}_{timestamp}{status_suffix}.{ext}

Examples:
  2.1.3_20260306_142300.pdf                    ← complete regular form
  2.6.1_EDP-03_20260306_142300.pdf             ← complete matrix form
  2.1.3_20260306_142300_PENDING_SUPERVISOR.pdf ← awaiting supervisor
  2.1.3_20260306_142300_PENDING_COUNCIL.pdf    ← awaiting council
  2.36.3_20260306_142300_PAUSED_3601.json      ← paused form (PIN=3601)
```

Each save produces both a `.pdf` and a `.json` with the same base name.

**Lifecycle cleanup**: When a form reaches `complete` status, the backend deletes all `_PENDING_*` files for that section. When it reaches `pending_council`, it deletes `_PENDING_SUPERVISOR` files.
