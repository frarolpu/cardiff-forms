import json

with open('forms_final.json', 'r') as f:
    data = json.load(f)

section = [x for x in data if x['section'] == '2.36.6'][0]
print(f"Section: {section['section']}")
print(f"Equipment: {section['equipment']}")
print(f"Drawing Ref: '{section['drawing_ref']}'")
print(f"Frequencies: {section['frequencies']}")
