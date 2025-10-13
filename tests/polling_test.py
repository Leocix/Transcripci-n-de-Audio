import time
import sys
import os

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

resp = client.post('/debug/create_test_job', json={'duration_seconds': 4})
print('create job status', resp.status_code, resp.text)
job = resp.json()
job_id = job.get('job_id')
print('job_id', job_id)

start = time.time()
while True:
    st = client.get(f'/status/{job_id}')
    print('status', st.status_code, st.json())
    if st.json().get('state') in ('done', 'error'):
        break
    if time.time() - start > 30:
        print('timeout waiting for job')
        break
    time.sleep(1)

print('finished')
