import urllib.request, json, urllib.error, re
req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/auth/google/', 
    data=json.dumps({'id_token': 'fake'}).encode(), 
    headers={'Content-Type': 'application/json'}
)
try:
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    html = e.read().decode('utf-8')
    match = re.search(r'<title>(.*?)</title>', html)
    if match:
        print("EXCEPTION:", match.group(1).strip())
    else:
        print("No title found.")
