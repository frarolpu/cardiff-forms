# Cardiff Forms — Documentation Hub

This folder contains the complete technical and functional documentation for the **Cardiff Forms** web application — a digital system for managing preventive maintenance inspection forms for the **Butetown Link Tunnel**, Cardiff.

---

## Documents

| File | Description |
|------|-------------|
| [architecture.md](architecture.md) | System architecture, tech stack, directory layout |
| [data-model.md](data-model.md) | JSON data structures, database schema, file naming |
| [workflow.md](workflow.md) | Form lifecycle, user roles, signing flow, passwords |
| [api-reference.md](api-reference.md) | All backend API endpoints with request/response examples |
| [frontend.md](frontend.md) | UI structure, JavaScript state, key functions |
| [deployment.md](deployment.md) | Local development, Docker, Render cloud deployment |

---

## Quick Summary

- **154 maintenance forms** extracted from the original DOCX document, covering sections 2.1.x → 2.45.x for the Butetown Link Tunnel
- **Three-role signing workflow**: Maintenance Engineer → Contractor Supervisor → Cardiff Council
- **Two storage modes**: PostgreSQL database (production) with automatic filesystem fallback
- **PDF generation** on every form save
- **Deployed on Render** (production) and runnable locally via Flask or a simple HTTP server

---

## Acronyms & Key Terms

| Term | Meaning |
|------|---------|
| EDP | Electrical Distribution Panel |
| EP | Electrical Point |
| VP | Ventilation Panel |
| FAN ID | Fan Identifier |
| Matrix form | A form that applies to multiple equipment items (uses a selector dropdown) |
| PENDING_SUPERVISOR | Form signed by engineer, awaiting supervisor |
| PENDING_COUNCIL | Form signed by engineer + supervisor, awaiting council |
| Paused form | Form saved mid-fill with a 4-digit PIN for later resumption |
