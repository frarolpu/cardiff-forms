import json

# Load both JSON files
with open('forms_parsed.json', 'r') as f:
    parsed = json.load(f)

with open('forms_final.json', 'r') as f:
    final = json.load(f)

# Create a mapping of section -> equipment
equipment_map = {}

# Extract equipment from raw_table
for form in parsed:
    section = form.get('section')
    raw_table = form.get('raw_table', [])
    
    # Equipment names are in the raw_table, usually in the first column
    # Skip header row (row 1), look for non-empty, non-drawing-ref values
    equipment_name = None
    
    if len(raw_table) > 2:
        for row_idx in range(2, min(len(raw_table), 8)):  # Check rows 2-7
            if raw_table[row_idx] and len(raw_table[row_idx]) > 0:
                cell_value = raw_table[row_idx][0].strip()
                # Skip empty cells, skip "DRG REF:", skip "STEP", "TASK"
                if cell_value and not cell_value.startswith('DRG REF') and cell_value not in ['STEP', 'TASK', ''] and cell_value.isalpha():
                    equipment_name = cell_value
                    break
    
    if equipment_name:
        equipment_map[section] = equipment_name

# Update forms_final.json with equipment data
for form in final:
    section = form.get('section')
    if section in equipment_map:
        form['equipment'] = equipment_map[section]

# Save updated forms_final.json
with open('forms_final.json', 'w') as f:
    json.dump(final, f, indent=2)

print(f"Updated {len(equipment_map)} forms with equipment data")
print("\nUnique equipment types found:")
unique_equipment = sorted(set(equipment_map.values()))
for eq in unique_equipment:
    count = list(equipment_map.values()).count(eq)
    print(f"  {eq}: {count} forms")
