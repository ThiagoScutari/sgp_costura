import requests
import json

url = "http://localhost:8001/api/planning/sync"

payload = {
    "pso_id": 13,
    "pulse_duration": 60,
    "batch_size": 82,
    "allocations": [
        {
            "operation_id": 1,
            "workstation_id": 1,
            "position": 1,
            "quantity": 82,
            "is_fraction": False
        }
    ],
    "version_name": "Teste_Script",
    "notes": "Teste via script"
}

try:
    print("Enviando request...")
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Erro: {e}")
