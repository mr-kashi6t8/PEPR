import urllib.request, urllib.error, json

def post(path):
    url = f'http://127.0.0.1:8000{path}'
    req = urllib.request.Request(url, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            body = r.read().decode('utf-8')
            print(path, 'STATUS', r.getcode())
            print('BODY', body)
    except urllib.error.HTTPError as e:
        try:
            print(path, 'HTTPERR', e.code)
            print('BODY', e.read().decode('utf-8'))
        except Exception:
            print(path, 'HTTPERR', e.code, 'no body')
    except Exception as ex:
        print(path, 'ERROR', str(ex))

if __name__ == '__main__':
    post('/api/v1/admin/ingestion/youtube_talkshows/run')
    post('/api/v1/admin/ingestion/worldbank_pakistan/run')
