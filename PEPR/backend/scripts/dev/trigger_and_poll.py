import urllib.request, urllib.error, json, time, sys

BASE = 'http://127.0.0.1:8000'

def post(path, timeout=30):
    url = f'{BASE}{path}'
    req = urllib.request.Request(url, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode('utf-8')
            return r.getcode(), json.loads(body)
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode('utf-8')
            return e.code, json.loads(body)
        except Exception:
            return e.code, {'error': 'no body'}
    except Exception as ex:
        return None, {'error': str(ex)}

def get(path, timeout=10):
    url = f'{BASE}{path}'
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read().decode('utf-8')
            return r.getcode(), json.loads(body)
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode('utf-8')
            return e.code, json.loads(body)
        except Exception:
            return e.code, {'error': 'no body'}
    except Exception as ex:
        return None, {'error': str(ex)}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python trigger_and_poll.py <source_id_or_uuid> [timeout_seconds]')
        sys.exit(1)
    source_id = sys.argv[1]
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 300

    code, body = post(f'/api/v1/admin/ingestion/{source_id}/run-async')
    print('/run-async', 'STATUS', code)
    print('BODY', json.dumps(body))
    if not body or 'result' not in body or 'run_id' not in body.get('result', {}):
        print('Failed to schedule run')
        sys.exit(1)
    run_id = body['result']['run_id']
    print('Scheduled run_id:', run_id)

    deadline = time.time() + timeout
    while time.time() < deadline:
        c, b = get(f'/api/v1/admin/ingestion/runs/{run_id}')
        if c != 200:
            print('Error polling run:', c, b)
            time.sleep(2)
            continue
        status = b.get('status')
        print('Run status:', status, 'records_fetched:', b.get('records_fetched'))
        if status and status.upper() != 'RUNNING':
            print('Final run result:', json.dumps(b))
            sys.exit(0)
        time.sleep(5)

    print('Timeout waiting for run to complete')
    sys.exit(2)
