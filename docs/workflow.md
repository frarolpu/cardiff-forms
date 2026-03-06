# Form Workflow

## Overview

Every maintenance form passes through up to four states before it is considered fully approved. The lifecycle enforces a role hierarchy where each role can only sign in sequence.

```
┌─────────┐     Engineer signs     ┌────────────────────┐
│   NEW   │ ─────────────────────► │ PENDING_SUPERVISOR │
└─────────┘                        └────────┬───────────┘
                                            │ Supervisor signs (password)
                                            ▼
                                   ┌────────────────────┐
                                   │  PENDING_COUNCIL   │
                                   └────────┬───────────┘
                                            │ Council signs (password)
                                            ▼
                                   ┌────────────────────┐
                                   │      COMPLETE      │
                                   └────────────────────┘

Alternatively, a form can be paused at any point:

┌─────────┐    User clicks         ┌────────────────┐
│   NEW   │ ──"Pause & Resume"───► │  PAUSED (PIN)  │
└─────────┘                        └───────┬────────┘
                                           │ User enters PIN
                                           ▼
                                   ┌───────────────┐
                                   │  Restored NEW │
                                   └───────────────┘
```

---

## User Roles

### Maintenance Engineer
- Opens the app, selects a form from the sidebar (All Forms tab)
- Fills in inspection date, inspector name, task checkboxes, comments, photos
- On matrix forms: selects the equipment item from the EDP/EP/VP/FAN/Sign dropdown
- Enters **name**, **initials** (≤ 3 chars), and **date** in the **Maintenance Engineer** box
- Clicks **Save** → form is saved as `PENDING_SUPERVISOR`
- Cannot interact with the Supervisor or Council boxes without a password

### Contractor Supervisor
- Switches to the **Pending Supervisor** tab in the sidebar
- Clicks on the pending form to load it — all engineer data is restored
- Clicks any input inside the **Contractor Supervisor** box
- Modal prompt appears: enters password **`Sice2026!`** and presses Unlock
- Fills in supervisor name, initials, date and any supervisor comments
- Clicks **Save** → form progresses to `PENDING_COUNCIL`

### Cardiff Council Representative
- Switches to the **Pending Council** tab in the sidebar
- Loads the pending-council form
- Clicks any input inside the **Council Approval** box
- Modal prompt appears: enters council password (same mechanism as supervisor)
- Fills in council name, initials, date and any approval comments
- Clicks **Save** → form saved as `COMPLETE`; all `_PENDING_*` files for that section are deleted

---

## Paused Forms

A form can be paused before engineer signing is complete (e.g., interrupted work):

1. Click **"Pause & Resume Later"** button (visible on form load)
2. A 4-digit PIN modal appears — the user notes the PIN
3. The form is saved as `*_PAUSED_{PIN}.json` in `saved_forms/`
4. To resume, open the **Paused Reports** tab → click the entry → enter PIN → form is restored

---

## Visual Status Indicators

| Sidebar Tab | Badge on Form | File suffix |
|---|---|---|
| All Forms | `✏️ NEW` | (none) |
| Pending Supervisor | `📋 PENDING – Awaiting Supervisor` | `_PENDING_SUPERVISOR` |
| Pending Council | `🏛️ PENDING – Awaiting Council` | `_PENDING_COUNCIL` |
| Paused Reports | `⏸️ PAUSED` | `_PAUSED_{PIN}` |
| (any, after both signed) | `✅ COMPLETE` | (none, base name) |

---

## Password Reference

| Role | Password |
|------|----------|
| Contractor Supervisor | `Sice2026!` |
| Cardiff Council | Same modal mechanism (password defined in JS) |

> **Security note**: Passwords are stored in plaintext in `index.html` (client-side JS). This is a convenience lock, not a cryptographic security measure. For real access control, move password validation to the backend.

---

## Special Form Types

### Matrix Forms (EDP / EP / VP / FAN ID / Sign)
- A single form definition covers multiple physical items
- A `<select>` dropdown (`#edpSelectorSection`) appears at the top of the form
- Choosing an item from the dropdown pre-fills or filters the task list (`updateTasksForEDP()`)
- The selected value is stored as `data.edp` in the saved JSON
- Filename includes the selected value: `2.6.1_EDP-03_20260306_142300.pdf`

### Cross Bore Door Forms (Sections 2.24.1–2.24.6)
- A separate selector (`#crossBoreDoorSection`) shows 7 door options
- The selected door is stored in `window.selectedCrossBoreDoor`

### Paused Forms
- Saved as JSON only (no PDF generated until the form is fully/partially completed)
- Identified by `_PAUSED_{4-digit-PIN}` in the filename

---

## Validation Rules

| Condition | Behaviour |
|---|---|
| Inspection date empty | Save blocked; error shown |
| Engineer name/initials/date empty | Save blocked when trying to submit for supervisor |
| Matrix form: no EDP selected | Save blocked |
| Supervisor section — clicking without password | Password modal shown |
| Wrong password entered | Error message in modal; field stays locked |
