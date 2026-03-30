import urllib.request, time, subprocess

# Start server in background
proc = subprocess.Popen(["python", "manage.py", "runserver", "127.0.0.1:8001"])
time.sleep(3)

try:
    req = urllib.request.Request("http://127.0.0.1:8001/static/admin/css/base.css")
    resp = urllib.request.urlopen(req, timeout=3)
    print("CSS HTTP STATUS:", resp.getcode())
    print("CSS LENGTH:", len(resp.read()))
except Exception as e:
    print("ERROR:", str(e))
finally:
    proc.terminate()
