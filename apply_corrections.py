"""
Apply frequency corrections from frequency_corrections.json to forms_final.json
"""

import json
import shutil

# Load corrections
with open('frequency_corrections.json', 'r', encoding='utf-8') as f:
    corrections = json.load(f)

# Load forms
with open('forms_final.json', 'r', encoding='utf-8') as f:
    forms = json.load(f)

# Backup original
shutil.copy('forms_final.json', 'forms_final_backup.json')
print("Backup created: forms_final_backup.json")

# Apply corrections
updated_count = 0
for form in forms:
    form_num = form['section']
    if form_num in corrections:
        old_freq = form.get('frequencies', [])
        new_freq = corrections[form_num]
        
        # Handle if new_freq is already a list
        if isinstance(new_freq, list):
            form['frequencies'] = new_freq
        else:
            form['frequencies'] = [new_freq]
        
        updated_count += 1
        if updated_count <= 10:  # Show first 10
            print(f"Updated {form_num}: {old_freq} -> {form['frequencies']}")

# Save updated forms
with open('forms_final.json', 'w', encoding='utf-8') as f:
    json.dump(forms, f, indent=2, ensure_ascii=False)

print(f"\nTotal updated: {updated_count} forms")
print("forms_final.json has been updated!")
