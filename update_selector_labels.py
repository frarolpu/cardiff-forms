"""
Update selector labels for specific forms:
- 2.6.1-2.6.4: Change EDP to EP (14 items)
- 2.31.1-2.31.4: Change EDP to VP (10 items)  
- 2.32.1-2.32.4: Change EDP to FAN ID (32 items with specific sequence)
"""

import json

# Load forms
with open('forms_final.json', 'r', encoding='utf-8') as f:
    forms = json.load(f)

# EP forms (2.6.1 - 2.6.4): 14 items
ep_forms = ["2.6.1", "2.6.2", "2.6.3", "2.6.4"]
ep_structure = [
    {"id": f"EP-{i:02d}", "name": f"EP-{i:02d}"} 
    for i in range(1, 15)
]

# VP forms (2.31.1 - 2.31.4): 10 items
vp_forms = ["2.31.1", "2.31.2", "2.31.3", "2.31.4"]
vp_structure = [
    {"id": f"VP-{i:02d}", "name": f"VP-{i:02d}"} 
    for i in range(1, 11)
]

# FAN ID forms (2.32.1 - 2.32.4): 32 items with specific sequence
fan_id_sequence = [
    "1-1", "1-2", "2-1", "2-2", "3-1", "3-2", "4-1", "4-2",
    "5-1", "5-2", "5-3", "5-4", "6-1", "6-2", "6-3", "6-4",
    "7-1", "7-2", "7-3", "7-4", "8-1", "8-2", "8-3", "8-4",
    "9-1", "9-2", "9-3", "9-4", "10-1", "10-2", "10-3", "10-4"
]
fan_id_structure = [
    {"id": f"FAN-{fid}", "name": f"FAN {fid}"} 
    for fid in fan_id_sequence
]

fan_id_forms = ["2.32.1", "2.32.2", "2.32.3", "2.32.4"]

# Process forms
for form in forms:
    section = form['section']
    
    if section in ep_forms:
        form['edps'] = ep_structure
        print(f"✅ {section}: Updated to 14 EP selectors")
    
    elif section in vp_forms:
        form['edps'] = vp_structure
        print(f"✅ {section}: Updated to 10 VP selectors")
    
    elif section in fan_id_forms:
        form['edps'] = fan_id_structure
        print(f"✅ {section}: Updated to 32 FAN ID selectors")

# Save updated forms
with open('forms_final.json', 'w', encoding='utf-8') as f:
    json.dump(forms, f, indent=2, ensure_ascii=False)

print(f"\n✅ Selector labels updated!")
print(f"   - 2.6.1-2.6.4: EP (14 items)")
print(f"   - 2.31.1-2.31.4: VP (10 items)")
print(f"   - 2.32.1-2.32.4: FAN ID (32 items)")
