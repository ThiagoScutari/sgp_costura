import urllib.request
import json

# Assuming planning_id 5 exists from previous context
url = "http://localhost:8001/api/planning/5/allocations"

try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")
