# Frontend Structure

## Overview

The entire frontend is contained in a single file: `index.html` (~3 300 lines).  
It uses **no external JavaScript framework** — only vanilla JS (ES2020), HTML5, and CSS3.

---

## Page Layout (HTML structure)

```
body
└── .wrapper                      (flex row)
    ├── .sidebar                  (fixed, left)
    │   ├── Tab buttons (All / Pending Supervisor / Pending Council / Paused)
    │   ├── .sidebar-search       (search input box)
    │   ├── Link → saved_forms.html
    │   ├── #formList             (All forms list)
    │   ├── #pendingSupervisorList
    │   ├── #pendingCouncilList
    │   └── #pausedFormsList
    │
    └── .main-content             (fluid, right)
        └── .container
            ├── #noFormSelected   (placeholder when nothing selected)
            └── #formContainer    (hidden until a form is selected)
                ├── .header       (logos + title + section info)
                └── .content
                    ├── #successMessage / #errorMessage
                    └── form#maintenanceForm
                        ├── General Information (date, inspector)
                        ├── #edpSelectorSection (matrix forms only)
                        ├── #crossBoreDoorSection (2.24.x forms only)
                        ├── Tasks (#taskList)
                        ├── Comments (engineer / supervisor / council)
                        ├── Materials Used
                        ├── Inspection Photos (before / after)
                        └── Approval (3 signature boxes)
                            ├── #engineerBox   (always active)
                            ├── #supervisorBox (disabled → unlocked by password)
                            └── #councilBox    (disabled → unlocked by password)

Modals (z-index: 9999, fixed):
  ├── #passwordModal        (Supervisor password)
  ├── #councilPasswordModal (Council password)
  ├── #pausePINModal        (Shows generated PIN after pausing)
  └── #resumeFormPINModal   (Enter PIN to resume paused form)
```

---

## JavaScript Global State

```js
let allForms = [];              // All 154 form objects from forms_final.json
let currentFormIndex = -1;      // Index into allForms of the currently-open form
let beforePhotos = [];          // Array of base64 data-URIs (before photos)
let afterPhotos = [];           // Array of base64 data-URIs (after photos)
let formStatus = 'new';         // 'new' | 'pending_supervisor' | 'pending_council' | 'complete'
let isPendingFormOpen = false;  // True when supervisor is editing a pending-supervisor form
let isPendingCouncilFormOpen = false; // True when council is editing a pending-council form
window.pendingFormData = null;       // Raw JSON of the loaded pending-supervisor form
window.pendingFormTasks = [];        // Tasks array of the loaded pending form
window.pendingCouncilFormData = null;// Raw JSON of the loaded pending-council form
window.selectedCrossBoreDoor = null; // Selected value for 2.24.x forms
```

---

## Key JavaScript Functions

### Initialisation

| Function | Description |
|----------|-------------|
| `loadForms()` | Fetches `forms_final.json`, populates `allForms`, calls `populateFormList()`, `loadPendingForms()`, `loadCouncilForms()`, `loadPausedForms()`, sets today as default date |
| `populateFormList()` | Renders `<li>` items in `#formList` for each form; attaches click → `selectForm(index)` |
| `loadPendingForms()` | `GET /api/pending-forms` → renders `#pendingSupervisorList` + updates badge count |
| `loadCouncilForms()` | `GET /api/council-forms` → renders `#pendingCouncilList` |
| `loadPausedForms()` | `GET /api/paused-forms` → renders `#pausedFormsList` |

### Navigation

| Function | Description |
|----------|-------------|
| `switchTab(tab)` | Switches sidebar view between `'all'`, `'pending-supervisor'`, `'pending-council'`, `'paused'` |
| `document.getElementById('searchForms').addEventListener('input', ...)` | Filters `#formList` items in real time by section number |

### Form Loading

| Function | Description |
|----------|-------------|
| `selectForm(index)` | Loads form at `allForms[index]`; renders tasks; shows EDP selector if `is_matrix`; resets photos/signatures |
| `updateTasksForEDP(value)` | Re-renders task list filtered to the selected EDP item |
| `loadPendingFormForSupervisor(formId)` | `GET /api/load-pending-form/{formId}` → restores all form fields; sets `isPendingFormOpen = true` |
| `loadPendingFormForCouncil(formId)` | Same as above but for council; sets `isPendingCouncilFormOpen = true` |
| `resumePausedForm(formId)` | Opens PIN entry modal; on success calls `GET /api/resume-paused-form/{pin}` and restores form |

### Form Saving

| Function | Description |
|----------|-------------|
| `saveFormToRepository()` | Main save function. Collects all field values into a JSON object, determines `status`, validates required fields, calls `POST /api/save-form`, handles response |
| `pauseForm()` | Generates a random 4-digit PIN, calls `POST /api/pause-form`, shows PIN modal |

### Password / Modal Handling

| Function | Description |
|----------|-------------|
| `validateSupervisorPassword()` | Reads `#supervisorPassword`, compares to hardcoded value; on success calls `unlockSupervisorSection()` |
| `unlockSupervisorSection()` | Removes `.disabled` class from `#supervisorBox`, adds `.active`, attaches input listeners |
| `validateCouncilPassword()` | Same pattern for council password modal |
| `closeSupervisorModal()` / `closeCouncilModal()` | Hides modals, clears password fields |
| `closePINModal()` / `closeResumePINModal()` / `validateResumePIN()` | Controls the pause/resume PIN modals |

### Utility

| Function | Description |
|----------|-------------|
| `resetForm()` | Clears all input fields, photo galleries, task checkboxes, resets state flags |
| `updateFormStatusBadge(status)` | Renders the coloured status pill at the top of the approval section |
| Photo drag-and-drop handlers | `addEventListener('dragover')`, `'drop'` on `.photo-upload` divs |
| `handlePhotoInput(event, type)` | Reads selected files as base64 and adds thumbnails to `beforePhotoGallery` / `afterPhotoGallery` |

---

## CSS Architecture

All styles are in a single `<style>` block inside `index.html`.

| Section | Coverage |
|---------|---------|
| Reset & base | `*`, `body`, `input/textarea` user-select |
| Layout | `.wrapper`, `.sidebar`, `.main-content`, `.container` |
| Sidebar | `.form-list`, `.form-item`, `.form-item.active`, `.pending-form-item` |
| Header | `.header`, `.header-logos`, `.header-title`, `.section-info` |
| Form sections | `.form-section`, `.form-row`, `.form-group`, labels, inputs |
| Tasks | `.task-list`, `.task-item`, checkbox styles |
| Photos | `.photo-upload` (drag-and-drop zone), `.photo-gallery`, `.photo-thumbnail` |
| Signature boxes | `.signature-row`, `.signature-box`, `.signature-box.disabled`, `.signature-box.active` |
| Modals | `.modal-overlay`, `.modal-content`, `.modal-password-group`, `.modal-actions` |
| Status badges | `.form-status-badge.pending`, `.complete` |
| Buttons | `.btn-primary`, `.btn-secondary`, `.btn-cancel`, `.btn-unlock` |
| Notifications | `.success-message`, `.error-message` |
| Print | `@media print` — hides sidebar and action buttons |
| Responsive (tablet) | `@media (max-width: 1024px)` |
| Responsive (mobile) | `@media (max-width: 768px)` |
| Responsive (small) | `@media (max-width: 480px)` |

---

## saved_forms.html

A companion page linked from the sidebar showing the list of all saved forms. It calls `GET /get-saved-forms` and renders a table with download links to `GET /api/download-form/<id>`.
