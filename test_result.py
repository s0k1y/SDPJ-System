import requests
import json

s = requests.Session()
r = s.post('http://localhost:8000/api/auth/login', json={'username': 'username', 'password': 'password'})

r = s.get('http://localhost:8000/api/reports/statistics')
print('Statistics:', json.dumps(r.json(), indent=2, ensure_ascii=False))

r = s.get('http://localhost:8000/api/reports/')
print('Reports:', json.dumps(r.json(), indent=2, ensure_ascii=False))

r = s.get('http://localhost:8000/api/detection/progress')
print('Progress:', json.dumps(r.json(), indent=2, ensure_ascii=False))
