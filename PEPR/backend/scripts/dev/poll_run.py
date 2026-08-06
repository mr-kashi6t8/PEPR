import urllib.request, urllib.error, json, time, sys

BASE = 'http://127.0.0.1:8000'

def get(path, timeout=10):
    url = f'{BASE}{path}'
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read().decode('utf-8')
            return r.getcode(), json.loads(body)
    except Exception as ex:
        return None, {'error': str(ex)}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python poll_run.py <run_id> [timeout_seconds]')
        sys.exit(1)
    run_id = sys.argv[1]
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 600
    deadline = time.time() + timeout
    while time.time() < deadline:
        code, body = get(f'/api/v1/admin/ingestion/runs/{run_id}')
        if code == 200:
            status = body.get('status')
            print(time.strftime('%Y-%m-%d %H:%M:%S'), 'status=', status, 'records=', body.get('records_fetched'))
            if status and status.upper() != 'RUNNING':
                print('Final:', json.dumps(body))
                sys.exit(0)
        else:
            print('Poll error:', code, body)
        time.sleep(5)
    print('Timeout waiting for run to complete')
    sys.exit(2)
