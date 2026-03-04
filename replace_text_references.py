"""
Replace EDP text references in form descriptions:
- 2.6.1-2.6.4: Replace "EDP" with "EP" in all text
- 2.31.1-2.31.4: Replace "EDP" with "VP" in all text  
- 2.32.1-2.32.4: Replace "EDP" with "FAN ID" in all text
"""

import json

def replace_in_text(text, old_term, new_term):
    """Replace term in text, case-insensitive"""
    if not text:
        return text
    # Replace EDP with new term (handle various cases)
    text = text.replace(old_term, new_term)
    text = text.replace(old_term.lower(), new_term)
    return text

# Load forms
with open('forms_final.json', 'r', encoding='utf-8') as f:
    forms = json.load(f)

# Configuration for replacements
replacements = {
    "2.6.1": ("EDP", "EP"),
    "2.6.2": ("EDP", "EP"),
    "2.6.3": ("EDP", "EP"),
    "2.6.4": ("EDP", "EP"),
    "2.31.1": ("EDP", "VP"),
    "2.31.2": ("EDP", "VP"),
    "2.31.3": ("EDP", "VP"),
    "2.31.4": ("EDP", "VP"),
    "2.32.1": ("EDP", "FAN ID"),
    "2.32.2": ("EDP", "FAN ID"),
    "2.32.3": ("EDP", "FAN ID"),
    "2.32.4": ("EDP", "FAN ID"),
}

# Process forms
for form in forms:
    section = form['section']
    
    if section in replacements:
        old_term, new_term = replacements[section]
        count = 0
        
        # Replace in equipment
        if 'equipment' in form and form['equipment']:
            original = form['equipment']
            form['equipment'] = replace_in_text(form['equipment'], old_term, new_term)
            if original != form['equipment']:
                count += 1
        
        # Replace in drawing_ref
        if 'drawing_ref' in form and form['drawing_ref']:
            original = form['drawing_ref']
            form['drawing_ref'] = replace_in_text(form['drawing_ref'], old_term, new_term)
            if original != form['drawing_ref']:
                count += 1
        
        # Replace in tasks
        for task in form.get('tasks', []):
            if 'description' in task:
                original = task['description']
                task['description'] = replace_in_text(task['description'], old_term, new_term)
                if original != task['description']:
                    count += 1
        
        print(f"✅ {section}: Replaced {old_term} → {new_term} ({count} changes)")

# Save updated forms
with open('forms_final.json', 'w', encoding='utf-8') as f:
    json.dump(forms, f, indent=2, ensure_ascii=False)

print(f"\n✅ Text references updated in all forms!")
