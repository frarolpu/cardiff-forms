"""
Recover form 2.1.5 from forms_parsed.json (Sheet 1 from 2.1.4 raw_table, Sheet 2 from separate entry),
convert letter-based steps to numeric, and add it to forms_final.json as a matrix form.
"""

import json
import re

# Load forms_parsed.json
with open('forms_parsed.json', 'r', encoding='utf-8') as f:
    forms_parsed = json.load(f)

tasks = []
letter_map = {
    'a': '1', 'b': '2', 'c': '3', 'd': '4', 'e': '5',
    'f': '6', 'g': '7', 'h': '8', 'i': '9', 'j': '10',
    'k': '11', 'l': '12', 'm': '13', 'n': '14', 'o': '15',
    'p': '16', 'q': '17', 'r': '18', 's': '19', 't': '20'
}

# SHEET 1: Find 2.1.5 Sheet 1 data in 2.1.4's raw_table
form_2_1_4 = next((f for f in forms_parsed if f.get('section') == '2.1.4'), None)
if form_2_1_4:
    raw_table = form_2_1_4.get('raw_table', [])
    
    print("📄 Reading Sheet 1 from 2.1.4 raw_table...")
    in_2_1_5_section = False
    
    for row in raw_table:
        if len(row) > 0:
            first_cell = row[0].strip() if row[0] else ""
            
            # Check for 2.1.5 Sheet 1 header
            if "Section   2.1.5" in str(row):
                in_2_1_5_section = True
                print("  Found 2.1.5 Sheet 1 header")
                continue
            
            # Extract task rows (format: "a)", "b)", etc.)
            if in_2_1_5_section and re.match(r'^[a-j]\)', first_cell):
                letter = first_cell[0]
                num = letter_map.get(letter, str(len(tasks) + 1))
                task_desc = row[1] if len(row) > 1 else ""
                
                if task_desc and "STEP" not in task_desc and "COMMENTS" not in task_desc:
                    tasks.append({
                        "step": num,
                        "description": task_desc.strip()
                    })
                    print(f"  Step {num} ({letter}): OK")

print(f"✅ Extracted {len(tasks)} tasks from Sheet 1")

# SHEET 2: Find 2.1.5 Sheet 2 in separate entry
form_2_1_5 = next((f for f in forms_parsed if f.get('section') == '2.1.5'), None)
if form_2_1_5:
    raw_table = form_2_1_5.get('raw_table', [])
    
    print("📄 Reading Sheet 2 from separate 2.1.5 entry...")
    
    for row in raw_table:
        if len(row) > 0:
            first_cell = row[0].strip() if row[0] else ""
            
            # Extract task rows (format: "k)", "l)", etc.)
            if re.match(r'^[k-r]\)', first_cell):
                letter = first_cell[0]
                num = letter_map.get(letter, str(len(tasks) + 1))
                task_desc = row[1] if len(row) > 1 else ""
                
                if task_desc and "STEP" not in task_desc and "COMMENTS" not in task_desc:
                    tasks.append({
                        "step": num,
                        "description": task_desc.strip()
                    })
                    print(f"  Step {num} ({letter}): OK")

print(f"✅ Total tasks extracted: {len(tasks)}")

if len(tasks) == 0:
    print("❌ No tasks extracted! Aborting.")
    exit(1)

# Clean up the form data
cleaned_form = {
    "section": "2.1.5",
    "equipment": "SWITCHBOARD / MAINS FAILURE TEST",
    "drawing_ref": "B8/1 to B8/6",
    "locations": ["WESTBOUND BORE", "EASTBOUND BORE", "COUNTY HALL", "SERVICE BUILDING", "FIRE PUMPING STATION"],
    "frequencies": ["WEEKLY", "MONTHLY", "3 MONTHLY", "6 MONTHLY", "ANNUALLY", "YEARLY"],
    "tasks": tasks,
    "is_matrix": True,
    "edps": [
        {"id": f"EDP-{i:02d}", "name": f"EDP-{i:02d}"} 
        for i in range(1, 15)
    ]
}

# Load forms_final.json
with open('forms_final.json', 'r', encoding='utf-8') as f:
    forms_final = json.load(f)

# Check if 2.1.5 already exists
existing_idx = next((i for i, f in enumerate(forms_final) if f['section'] == '2.1.5'), None)

if existing_idx is not None:
    # Replace existing
    forms_final[existing_idx] = cleaned_form
    print(f"✅ Updated existing form 2.1.5 at index {existing_idx}")
else:
    # Find correct position (after 2.1.4)
    idx_2_1_4 = next((i for i, f in enumerate(forms_final) if f['section'] == '2.1.4'), None)
    if idx_2_1_4 is not None:
        forms_final.insert(idx_2_1_4 + 1, cleaned_form)
        print(f"✅ Inserted form 2.1.5 at index {idx_2_1_4 + 1}")
    else:
        # Add at beginning
        forms_final.insert(0, cleaned_form)
        print(f"✅ Inserted form 2.1.5 at index 0")

# Save updated forms
with open('forms_final.json', 'w', encoding='utf-8') as f:
    json.dump(forms_final, f, indent=2, ensure_ascii=False)

print(f"\n✅ Form 2.1.5 recovered and added to forms_final.json!")
print(f"   - Section: 2.1.5")
print(f"   - Equipment: {cleaned_form['equipment']}")
print(f"   - Tasks: {len(tasks)} (converted from letters a-{chr(ord('a')+len(tasks)-1)} to numbers)")
print(f"   - Matrix: Yes (14 EDPs)")
print(f"   - Total forms now: {len(forms_final)}")
