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
    
    # Look for "EQUIPMENT/SYSTEM" in the header row (usually row 1)
    equipment_value = None
    header_row_idx = None
    
    # Find the header row
    for idx, row in enumerate(raw_table):
        if row and len(row) > 0 and 'EQUIPMENT/SYSTEM' in row[0]:
            header_row_idx = idx
            break
    
    # If we found the header, look for the equipment value in subsequent rows
    if header_row_idx is not None:
        for row_idx in range(header_row_idx + 1, min(header_row_idx + 10, len(raw_table))):
            if raw_table[row_idx] and len(raw_table[row_idx]) > 0:
                cell_value = raw_table[row_idx][0].strip()
                # Skip empty cells, skip anything starting with "DRG REF", "TEXT REF", skip "STEP", "TASK"
                if (cell_value and 
                    not cell_value.startswith('DRG REF') and 
                    not cell_value.startswith('TEXT REF') and
                    cell_value not in ['STEP', 'TASK', ''] and
                    not cell_value.startswith('SHEET') and
                    not cell_value.startswith('Section') and
                    not cell_value.startswith('MAINTENANCE') and
                    not cell_value.startswith('Butetown')):
                    equipment_value = cell_value
                    break
    
    if equipment_value:
        equipment_map[section] = equipment_value
        print(f"Section {section}: {equipment_value}")

# Update forms_final.json with equipment data
for form in final:
    section = form.get('section')
    if section in equipment_map:
        form['equipment'] = equipment_map[section]

# Save updated forms_final.json
with open('forms_final.json', 'w') as f:
    json.dump(final, f, indent=2)

print(f"\n✓ Updated {len(equipment_map)} forms with equipment data")
print("\nUnique equipment/system types found:")
unique_equipment = sorted(set(equipment_map.values()))
for eq in unique_equipment:
    count = list(equipment_map.values()).count(eq)
    print(f"  {eq}: {count} forms")
