"""
Remove matrix structure from form 2.1.5 - it should be a regular form with 18 tasks
"""

import json

# Load forms_final.json
with open('forms_final.json', 'r', encoding='utf-8') as f:
    forms = json.load(f)

# Find and update 2.1.5
for form in forms:
    if form['section'] == '2.1.5':
        # Remove matrix structure
        if 'is_matrix' in form:
            del form['is_matrix']
        if 'edps' in form:
            del form['edps']
        
        print(f"✅ Removed matrix structure from 2.1.5")
        print(f"   - Tasks: {len(form['tasks'])}")
        print(f"   - is_matrix: removed")
        print(f"   - edps: removed")
        break

# Save updated forms
with open('forms_final.json', 'w', encoding='utf-8') as f:
    json.dump(forms, f, indent=2, ensure_ascii=False)

print(f"\n✅ Form 2.1.5 updated - Now a regular form (no selector)")
