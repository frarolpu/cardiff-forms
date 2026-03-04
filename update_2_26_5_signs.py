"""
Update form 2.26.5 to use Sign selector with specific sign locations instead of EDPs
"""

import json

# Sign locations for 2.26.5
signs = [
    # Gantry 1
    {"id": "EB-L1-G1-V43513", "name": "#EB Lane 1 Gantry 1 V43513 Type 9421"},
    {"id": "EB-L2-G1-V43514", "name": "#EB Lane 2 Gantry 1 V43514 Type 9421"},
    {"id": "WB-L1-G1-V43523", "name": "#WB Lane 1 Gantry 1 V43523 Type 9421"},
    {"id": "WB-L2-G1-V43524", "name": "#WB Lane 2 Gantry 1 V43524 Type 9421"},
    
    # Gantry 2
    {"id": "EB-L1-G2-V42311", "name": "#EB Lane 1 Gantry 2 V42311 Type 9421"},
    {"id": "EB-L2-G2-V42411", "name": "#EB Lane 2 Gantry 2 V42411 Type 9421"},
    {"id": "WB-L1-G2-V43517", "name": "#WB Lane 1 Gantry 2 V43517 Type 9421"},
    {"id": "WB-L2-G2-V434518", "name": "#WB Lane 2 Gantry 2 V434518 Type 9421"},
    
    # Gantry 3
    {"id": "EB-L1-G3-V42312", "name": "#EB Lane 1 Gantry 3 V42312 Type 9421"},
    {"id": "EB-L2-G3-V42412", "name": "#EB Lane 2 Gantry 3 V42412 Type 9421"},
    {"id": "WB-L1-G3-V43515", "name": "#WB Lane 1 Gantry 3 V43515 Type 9421"},
    {"id": "WB-L2-G3-V43516", "name": "#WB Lane 2 Gantry 3 V43516 Type 9421"},
    
    # EB Posts
    {"id": "EB-Post-L1-V42313", "name": "EB Post Lane 1 V42313 Type 9409"},
    {"id": "EB-Post-L2-V42413", "name": "EB Post Lane 2 V42413 Type 9409"},
    
    # EB Entry
    {"id": "EB-Entry-L1-V42314", "name": "#EB Entry Lane 1 V42314 Type 9421G"},
    {"id": "EB-Entry-L2-V42414", "name": "#EB Entry Lane 2 V42414 Type 9421G"},
    
    # EB Exit
    {"id": "EB-Exit-L1-V42317", "name": "#EB Exit Lane 1 V42317 Type 9421G"},
    {"id": "EB-Exit-L2-V42417", "name": "#EB Exit Lane 2 V42417 Type 9421G"},
    
    # WB Posts
    {"id": "WB-Post-L1-V43433", "name": "WB Post Lane 1 V43433 Type 9409"},
    {"id": "WB-Post-L2-V43434", "name": "WB Post Lane 2 V43434 Type 9409"},
    
    # WB Gantry 4
    {"id": "WB-L1-G4-V43431", "name": "WB Lane 1 Gantry 4 V43431 Type 9421"},
    {"id": "WB-L2-G4-V43432", "name": "WB Lane 2 Gantry 4 V43432 Type 9421"},
    
    # WB Entry
    {"id": "WB-Entry-L1-V42111", "name": "#WB Entry Lane 1 V42111 Type 9421G"},
    {"id": "WB-Entry-L2-V42211", "name": "#WB Entry Lane 2 V42211 Type 9421G"},
    
    # WB Exit
    {"id": "WB-Exit-L1-V42114", "name": "#WB Exit Lane 1 V42114 Type 9421G"},
    {"id": "WB-Exit-L2-V42214", "name": "#WB Exit Lane 2 V42214 Type 9421G"},
    
    # WB Ferry Rd
    {"id": "WB-Ferry-L1-V43521", "name": "WB Ferry Rd slip Lane 1 V43521 Type 9409"},
    {"id": "WB-Ferry-L2-V43522", "name": "WB Ferry Rd slip Lane 2 V43522 Type 9409"},
    
    # Culverhouse Cross
    {"id": "CC-L1-V33131", "name": "#Culverhouse Cross L1 V33131 Type 9409"},
    {"id": "CC-L2-V33132", "name": "#Culverhouse Cross L2 V33132 Type 9409"},
    
    # EB C/Reservation P45
    {"id": "EB-CR-P45-L1-V33133", "name": "#EB C/Reservation P45 L1 V33133 Type 9409"},
    {"id": "WB-CR-P45-L2-V33134", "name": "#WB C/Reservation P45 L2 V33134 Type 9409"},
    
    # EB C/Reservation P80
    {"id": "EB-CR-P80-L1-V33135", "name": "#EB C/Reservation P80 L1 V33135 Type 9409"},
    {"id": "WB-CR-P80-L2-V33136", "name": "#WB C/Reservation P80 L2 V33136 Type 9409"},
    
    # EB C/Reservation P104
    {"id": "EB-CR-P104-L1-V33111", "name": "#EB C/Reservation P104 L1 V33111 Type 9409"},
    {"id": "WB-CR-P104-L2-V33112", "name": "#WB C/Reservation P104 L2 V33112 Type 9409"},
    
    # EB C/Reservation P130
    {"id": "EB-CR-P130-L1-V33113", "name": "#EB C/Reservation P130 L1 V33113 Type 9409"},
    {"id": "WB-CR-P130-L2-V33114", "name": "#WB C/Reservation P130 L2 V33114 Type 9409"},
    
    # Leckwith WB Slip
    {"id": "Leck-WB-Slip-L1-V33121", "name": "#Leckwith WB Slip L1 V33121 Type 9409"},
    {"id": "Leck-WB-Slip-L2-V33122", "name": "#Leckwith WB Slip L2 V33122 Type 9409"},
    
    # Leckwith EB Entry Slip
    {"id": "Leck-EB-Entry-L1-V33115", "name": "#Leckwith EB Entry Slip L1 V33115 Type 9409"},
    {"id": "Leck-EB-Entry-L2-V33116", "name": "#Leckwith EB Entry Slip L2 V33116 Type 9409"},
    
    # EB C/Reservation P159
    {"id": "EB-CR-P159-L1-V33117", "name": "#EB C/Reservation P159 L1 V33117 Type 9409"},
    {"id": "WB-CR-P159-L2-V33118", "name": "#WB C/Reservation P159 L2 V33118 Type 9409"},
    
    # EB C/Reservation P180
    {"id": "EB-CR-P180-L1-V43511", "name": "#EB C/Reservation P180 L1 V43511 Type 9409"},
    {"id": "WB-CR-P180-L2-V43512", "name": "#WB C/Reservation P180 L2 V43512 Type 9409"},
]

# Load forms_final.json
with open('forms_final.json', 'r', encoding='utf-8') as f:
    forms = json.load(f)

# Find and update 2.26.5
for form in forms:
    if form['section'] == '2.26.5':
        form['edps'] = signs  # Use 'edps' key but with sign data
        print(f"✅ Updated form 2.26.5 with Sign selector")
        print(f"   - Total signs: {len(signs)}")
        print(f"   - is_matrix: {form.get('is_matrix', False)}")
        break

# Save updated forms
with open('forms_final.json', 'w', encoding='utf-8') as f:
    json.dump(forms, f, indent=2, ensure_ascii=False)

print(f"\n✅ Form 2.26.5 updated!")
print(f"   - Selector type: Sign (not EDP)")
print(f"   - Total sign locations: {len(signs)}")
