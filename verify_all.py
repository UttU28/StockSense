import requests
import sys

BASE_URL = 'http://localhost:8000'

def check(name, result):
    print(f'[{ "PASS" if result else "FAIL" }] {name}')
    if not result: sys.exit(1)

print('--- Checking Chart Frontend ---')
try:
    r = requests.get(f'{BASE_URL}/chart?symbol=NVDA')
    check('Chart endpoint 200 OK', r.status_code == 200)
    print(f'DEBUG: Actual Text Length: {len(r.text)}')
    check('Inlined JS present (>100KB)', len(r.text) > 100000)
    check('Correct API Endpoint used In HTML', '/chart_api/history/' in r.text)
except Exception as e:
    print(f'FAIL Chart: {e}')
    sys.exit(1)

print('\n--- Checking Data Backend ---')
try:
    r = requests.get(f'{BASE_URL}/chart_api/history/NVDA')
    check('Data API endpoint 200 OK', r.status_code == 200)
    check('Data has content', len(r.json()) > 0)
except Exception as e:
    print(f'FAIL Data API: {e}')
    sys.exit(1)

print('\n--- ALL SYSTEMS GO ---')
