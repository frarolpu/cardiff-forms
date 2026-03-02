import json

forms = json.load(open('forms_final.json'))
f = next((f for f in forms if f['section'] == '2.36.6'), None)

if f:
    print('Form 2.36.6:')
    print(f"  Equipment: {f['equipment']}")
    print(f"  Frequency: {f['frequencies']}")
    print(f"  Locations: {f['locations']}")
else:
    print("Form 2.36.6 not found")
