import io, zipfile, urllib.request, json, time

# Test zip olustur
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w") as zf:
    zf.writestr("main.py", "def hello():\n    return 'world'\n\nclass App:\n    def run(self):\n        print(hello())\n")
    zf.writestr("utils.py", "def helper(x):\n    return x * 2\n\nclass Config:\n    debug = True\n")
zip_bytes = buf.getvalue()

# API cagris
boundary = "----TestBoundary"
body = b"\r\n".join([
    f"--{boundary}".encode(),
    b"Content-Disposition: form-data; name=\"provider\"\r\n\r\ngemini",
    f"--{boundary}".encode(),
    b"Content-Disposition: form-data; name=\"use_nlp\"\r\n\r\nfalse",
    f"--{boundary}".encode(),
    b"Content-Disposition: form-data; name=\"file\"; filename=\"test.zip\"\r\nContent-Type: application/zip\r\n\r\n" + zip_bytes,
    f"--{boundary}--".encode(),
])

req = urllib.request.Request(
    "http://localhost:8000/analysis/upload",
    data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    method="POST",
)

print("API'ye istek gonderiliyor...")
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode())
    print("LLM Provider:", data.get("llm_provider", "yok"))
    print("Uyarilar:", data.get("warnings", []))
    summary = data.get("summary", "")
    print("Ozet (ilk 200 karakter):", summary[:200])
    print("Mermaid basliyor mu:", data.get("mermaid", "")[:80])
    print("TEST BASARILI")
except urllib.request.HTTPError as e:
    print("HTTP Hata:", e.code, e.read().decode())
except Exception as e:
    print("Hata:", e)
