import requests
import json

data = {
    "section": "2.36.6",
    "equipment": "TEST",
    "drawing_ref": "",
    "locations": [],
    "frequencies": [],
    "inspectionDate": "2026-02-19",
    "inspector": "Test",
    "comments": "Test",
    "tasks": [],
    "signatures": {},
    "photos": []
}

response = requests.post(
    'http://127.0.0.1:5000/api/save-form',
    json=data,
    headers={'Content-Type': 'application/json'}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
