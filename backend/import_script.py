import urllib.request
import mimetypes
import uuid
import os

url = "http://localhost:8000/api/pso/import"
filename = "test_pso.pdf"
boundary = uuid.uuid4().hex

data = []
data.append(f'--{boundary}')
data.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"')
data.append('Content-Type: application/pdf')
data.append('')

with open(filename, 'rb') as f:
    data.append(f.read().decode('latin-1')) # Decode bits to string for concatenation

data.append(f'--{boundary}--')
data.append('')

body = '\r\n'.join(data).encode('latin-1')

req = urllib.request.Request(url, data=body)
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

try:
    with urllib.request.urlopen(req) as response:
        print(f"Status: {response.status}")
        print(response.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
