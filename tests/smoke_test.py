from fastapi.testclient import TestClient
import sys
import os

# Ajustar path para importar main
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from main import app

client = TestClient(app)

def test_health():
    resp = client.get('/health')
    print('STATUS CODE:', resp.status_code)
    print('JSON:', resp.json())
    assert resp.status_code == 200

if __name__ == '__main__':
    test_health()
