"""可莉 TTS 本地服务：GPT-SoVITS 可莉专属微调模型（来自 HF Space baicai1145/Genshin_A-L, trained/可莉），CPU 推理。
GET http://127.0.0.1:8765/tts?text=...  -> {"file": ".../cache/<md5>.wav"}"""
import hashlib, json, sys, threading, soundfile as sf
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path
D = Path(__file__).parent; sys.path.insert(0, str(D / "sovits"))
import klee_sv as K
C = D / "cache"; C.mkdir(exist_ok=True); L = threading.Lock()
def synth(text):
    f = C / (hashlib.md5(text.encode()).hexdigest() + ".wav")
    if not f.exists():
        with L:
            sr, a = K.synth(text)
        sf.write(f, a, sr)
    return str(f)
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        t = (parse_qs(urlparse(self.path).query).get("text") or [""])[0].strip()[:80]
        try: body, code = json.dumps({"file": synth(t)} if t else {"ok": True}).encode(), 200
        except Exception as e: body, code = json.dumps({"error": str(e)}).encode(), 500
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass
ThreadingHTTPServer(("127.0.0.1", 8765), H).serve_forever()
