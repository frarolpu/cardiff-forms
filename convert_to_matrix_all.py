"""
Convert multiple forms to matrix format with EDP dropdowns.
Also consolidates forms with multiple pages.
"""

import json
from collections import defaultdict

# Forms to convert to matrix
MATRIX_FORMS = [
    "2.5.1", "2.5.2", "2.5.4", "2.5.5", "2.5.6",
    "2.6.1", "2.6.2", "2.6.3", "2.6.4",
    "2.11.2", "2.22.1", "2.22.2", "2.22.3",
    "2.23.1", "2.23.2", "2.23.3",
    "2.26.5", "2.31.1", "2.31.2", "2.31.3", "2.31.4",
    "2.32.1", "2.32.2", "2.32.3", "2.32.4", "2.32.5", "2.32.6"
]

# Forms with multiple pages (need task consolidation)
MULTI_PAGE_FORMS = {
    "2.1.5", "2.5.6", "2.6.1", "2.6.2", "2.6.3", "2.6.4", 
    "2.11.2", "2.32.3", "2.32.4"
}

# Load forms
with open('forms_final.json', 'r', encoding='utf-8') as f:
    forms = json.load(f)

# Group forms by section to identify duplicates
forms_by_section = defaultdict(list)
for i, form in enumerate(forms):
    forms_by_section[form['section']].append((i, form))

# Create standard EDP structure
edps_structure = [
    {"id": f"EDP-{i:02d}", "name": f"EDP-{i:02d}"} 
    for i in range(1, 15)
]

# Process forms
indices_to_remove = []

for section in MATRIX_FORMS:
    if section in forms_by_section:
        entries = forms_by_section[section]
        
        if len(entries) > 1:
            print(f"\n📋 Form {section}: {len(entries)} entries found")
            
            if section in MULTI_PAGE_FORMS:
                print(f"   ⚠️ Multi-page form - consolidating {len(entries)} entries...")
                
                # Consolidate: merge all tasks, remove duplicates
                consolidated_tasks = {}
                main_form = entries[0][1]
                
                for idx, form_entry in entries:
                    for task in form_entry['tasks']:
                        task_key = task['step']
                        if task_key not in consolidated_tasks:
                            consolidated_tasks[task_key] = task
                
                # Sort by step number
                try:
                    sorted_tasks = sorted(
                        consolidated_tasks.values(),
                        key=lambda x: (int(x['step'].split('.')[0]), 
                                      int(x['step'].split('.')[-1]) if '.' in x['step'] else 0)
                    )
                except:
                    sorted_tasks = list(consolidated_tasks.values())
                
                main_form['tasks'] = sorted_tasks
                main_form['is_matrix'] = True
                main_form['edps'] = edps_structure
                
                print(f"   ✅ Consolidated to {len(sorted_tasks)} unique tasks")
                
                # Mark other entries for removal
                for idx, _ in entries[1:]:
                    indices_to_remove.append(idx)
                    print(f"   🗑️ Removing duplicate entry at index {idx}")
            else:
                # Single page forms found multiple times - just use first, remove rest
                print(f"   ⚠️ Multiple entries found, keeping first and removing duplicates")
                main_form = entries[0][1]
                main_form['is_matrix'] = True
                main_form['edps'] = edps_structure
                
                for idx, _ in entries[1:]:
                    indices_to_remove.append(idx)
                    print(f"   🗑️ Removing duplicate entry at index {idx}")
        else:
            # Single entry - just add matrix structure
            idx, form = entries[0]
            form['is_matrix'] = True
            form['edps'] = edps_structure
            print(f"✅ Form {section}: Added matrix structure ({len(form['tasks'])} tasks)")

# Remove duplicate entries (in reverse order to preserve indices)
for idx in sorted(indices_to_remove, reverse=True):
    print(f"Removing index {idx}: {forms[idx]['section']}")
    del forms[idx]

# Save updated forms
with open('forms_final.json', 'w', encoding='utf-8') as f:
    json.dump(forms, f, indent=2, ensure_ascii=False)

print(f"\n✅ Conversion complete!")
print(f"   - Converted {len(MATRIX_FORMS)} forms to matrix format")
print(f"   - Consolidated {len(MULTI_PAGE_FORMS)} multi-page forms")
print(f"   - Removed {len(indices_to_remove)} duplicate entries")
print(f"   - Total forms now: {len(forms)}")
