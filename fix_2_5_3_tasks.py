"""
Update form 2.5.3 to 14 tasks (remove task 15, renumber correctly)
"""

import json

with open('forms_final.json', 'r', encoding='utf-8') as f:
    forms = json.load(f)

for form in forms:
    if form['section'] == '2.5.3':
        # Keep only 14 tasks (remove the 15th)
        form['tasks'] = [
            {"step": "1", "description": "Check distribution panel to ensure that it is free from obvious faults"},
            {"step": "2", "description": "Check all electrical connections including earth bonding and test the latter to ensure that a good earth path exists"},
            {"step": "3", "description": "Clean interiors and check for signs of overheating and condensation within panel"},
            {"step": "4", "description": "Check the heater/thermostat is operational 15oC"},
            {"step": "5", "description": "Check the operation and lubricate interlocks along with hinges"},
            {"step": "6", "description": "Check that tunnel low temperature thermostats above DP 1 and 14 function correctly, by setting lighting level to stage 1 and operating thermostat - lighting should ramp up to stage 3 and generate an alarm on the EPCMS"},
            {"step": "7", "description": "Check that earth connections are secure and tight"},
            {"step": "8", "description": "Carry out functional tests on RCD units using proprietary testing equipment"},
            {"step": "9", "description": "Check that UPS emergency lighting phase failure monitoring relay operates on loss of supply in DP 1 and 14"},
            {"step": "10", "description": "Check cable glands for signs of water ingress."},
            {"step": "11", "description": "Check all cable markers are in place and legible"},
            {"step": "13", "description": "Operate panel circuit breakers/switches in turn to ensure correct operation."},
            {"step": "14", "description": "Isolate supplies in conjunction with CCC and implement a thorough check on security of terminations"},
            {"step": "15", "description": "Clean panel exterior with proprietary stainless steel cleaning agent."}
        ]
        
        print("✅ Updated form 2.5.3:")
        print(f"   - Tasks: 14 (steps 1-11, 13-15)")
        print(f"   - Task 12 removed (not in document)")
        break

with open('forms_final.json', 'w', encoding='utf-8') as f:
    json.dump(forms, f, indent=2, ensure_ascii=False)

print("\n✅ forms_final.json updated!")
