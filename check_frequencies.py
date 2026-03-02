import json

forms = json.load(open('forms_final.json'))
multi = [f for f in forms if len(f.get('frequencies', [])) > 1]

print(f'Total forms: {len(forms)}')
print(f'Forms with multiple frequencies: {len(multi)}')

if multi:
    print('\nForms with multiple frequencies:')
    for f in multi[:20]:
        print(f"  {f['section']}: {f['frequencies']}")
    if len(multi) > 20:
        print(f'  ... and {len(multi) - 20} more')
else:
    print('\n✓ All forms have exactly one frequency!')
