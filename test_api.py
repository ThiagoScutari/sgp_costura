import urllib.request
import json
import urllib.error

url = "http://localhost:8001/api/production/start"
data = {"planning_id": 5}
headers = {'Content-Type': 'application/json'}

try:
    print(f"Sending POST to {url}...")
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
    with urllib.request.urlopen(req) as response:
        print(f"Status Code: {response.getcode()}")
        print(f"Response: {response.read().decode('utf-8')}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.read().decode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")
