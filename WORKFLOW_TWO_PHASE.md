# Two-Phase Signature Workflow

## Overview
The Cardiff Forms maintenance system now implements a two-phase signature workflow with password protection for supervisor access. This ensures proper control and verification of maintenance forms.

## Workflow Phases

### Phase 1: Engineer Signing (NEW Form)
1. **Access Form**: Maintenance Engineer selects a maintenance form from the sidebar
2. **Form Status**: Badge displays "✏️ NEW - Engineer Signing"
3. **Fill Engineering Data**:
   - Inspection date
   - Inspector name
   - Select EDP/EP/VP/FAN ID/Sign (for matrix forms)
   - Complete tasks (checkboxes)
   - Add comments
   - Upload photos
4. **Engineer Signature**:
   - Enter Full Name
   - Enter Initials (max 3 chars)
   - Confirm Date (auto-populated to today)
5. **Contractor Supervisor Section**: Greyed out and disabled
6. **Save Form**:
   - Click "Save" button
   - System validates engineer signature is complete
   - Form saves as **PENDING** status
   - Success message: "✓ Form saved as PENDING! Ready for Supervisor signature"
   - Form resets for new entry

### Phase 2: Supervisor Completion (PENDING Form)
1. **Access Pending Form**: Supervisor needs to open the pending form
   - API endpoint: GET `/api/pending-forms` lists all pending forms
   - Call GET `/api/load-pending-form/{form_id}` to load form data
2. **Form Status Badge**: "📋 PENDING - Awaiting Supervisor"
3. **Unlock Supervisor Section**:
   - Attempt to click any field in Contractor Supervisor section
   - Password modal appears
   - Enter password: `Sice2026!`
   - Press Enter or click "Unlock"
4. **Complete Supervisor Data**:
   - Supervisor Full Name
   - Supervisor Initials (max 3 chars)
   - Confirm Date
5. **Save Form as Complete**:
   - Click "Save" button
   - System detects both engineer AND supervisor have signed
   - Form saves as **COMPLETE** status
   - Success message: "✓ Form COMPLETED and saved!"
   - Form resets

## Password Protection

- **Password**: `Sice2026!`
- **Purpose**: Protects Supervisor section from unauth access
- **Modal Interactions**:
  - Press Escape to close
  - Click outside modal to close
  - Press Enter to submit password
  - Incorrect password shows error

## File Naming Convention

### New Engineer-Signed Forms (PENDING)
```
{section}_{selector}_{timestamp}_PENDING.pdf
2.1.1_2025-02-19_161234_PENDING.pdf    (non-matrix)
2.6.1_EP-05_2025-02-19_161234_PENDING.pdf  (matrix with selector)
```

### Complete Forms (COMPLETE)
```
{section}_{selector}_{timestamp}.pdf
2.1.1_2025-02-19_161234.pdf             (non-matrix)
2.6.1_EP-05_2025-02-19_161234.pdf       (matrix with selector)
```

## API Endpoints

### Get Pending Forms
```
GET /api/pending-forms
Response:
{
  "success": true,
  "count": 5,
  "forms": [
    {
      "id": 42,
      "filename": "2.1.1_20250219_161234_PENDING.pdf",
      "section": "2.1.1",
      "status": "pending",
      "created_at": "2025-02-19T16:12:34.000Z"
    },
    ...
  ]
}
```

### Load Pending Form
```
GET /api/load-pending-form/{form_id}
Response:
{
  "success": true,
  "data": {
    "section": "2.1.1",
    "equipment": "Tunnel Lights",
    "inspectionDate": "2025-02-19",
    "inspector": "John Doe",
    "status": "pending",
    "signatures": {
      "engineer": "John Doe",
      "engineerInitials": "JD",
      "engineerDate": "2025-02-19",
      "supervisor": "",
      "supervisorInitials": "",
      "supervisorDate": ""
    },
    ...
  },
  "filename": "2.1.1_20250219_161234_PENDING.pdf",
  "status": "pending"
}
```

## Key Features

### Form Status Tracking
- **NEW**: Engineer is filling out the form
- **PENDING**: Engineer has saved, awaiting supervisor
- **COMPLETE**: Both engineer and supervisor have signed

### Validation
- Engineer signature (name, initials, date) required before saving
- Supervisor section disabled until password is entered
- Form status determined by which signatures are present

### Visual Indicators
- Supervisor section styled with reduced opacity (0.5) when disabled
- Status badge shows current form state
- Input fields disabled/enabled based on form status

## User Roles

### Maintenance Engineer
- Fills out maintenance tasks
- Enters own signature
- Cannot edit supervisor section initially
- Saves form as PENDING

### Contractor Supervisor
- Accesses pending forms with password
- Enters supervisor signature
- Completes the form
- Saves form as COMPLETE

## Database Schema

### saved_forms Table
```sql
CREATE TABLE IF NOT EXISTS saved_forms (
    id SERIAL PRIMARY KEY,
    section VARCHAR(50),
    filename VARCHAR(255),
    status VARCHAR(20) DEFAULT 'complete',
    pdf_data BYTEA,
    form_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

- **status**: 'pending' or 'complete'
- **form_data**: Full JSON form data for restoration
- **pdf_data**: Generated PDF file

## Implementation Details

### Frontend (index.html)
- Global state: `isPendingFormOpen`, `formStatus`
- CSS classes: `.disabled`, `.active` for signature boxes
- Modal with password validation
- Event listeners for Escape, click-outside, Enter keys

### Backend (app.py)
- Modified save endpoint to handle status
- New `/api/pending-forms` endpoint
- New `/api/load-pending-form/{id}` endpoint
- Database stores both PDF and JSON form data

## Testing Checklist

- [ ] Engineer can fill form and see supervisor section is disabled
- [ ] Clicking supervisor input shows password modal
- [ ] Wrong password shows error
- [ ] Correct password (Sice2026!) enables supervisor section
- [ ] Pressing Escape closes modal
- [ ] Entering password via Enter key works
- [ ] Form saves as PENDING with Engineer signature
- [ ] Supervisor can access pending forms list
- [ ] Loading pending form restores all engineer data
- [ ] Supervisor can complete form
- [ ] Form saves as COMPLETE with both signatures
- [ ] PDF filename includes PENDING/COMPLETE status
- [ ] Form resets after save, supervisor section disabled again

## Future Enhancements

1. Email notification to supervisor when form is pending
2. Supervisor dashboard showing all pending forms
3. Form history/audit trail
4. Signature image capture (currently text-based)
5. Digital signature certificate support
6. Form expiration reminder (pending > X days)
7. Role-based access control in UI
8. Form routing based on equipment type
9. Bulk form operations
10. Advanced analytics/reporting
