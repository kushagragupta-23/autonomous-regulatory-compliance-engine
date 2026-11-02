import sys
import os
import webbrowser
import threading
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

PORT = 8005

def open_browser():
    time.sleep(1.5)
    print(f"\n[+] Opening browser at http://127.0.0.1:{PORT} ...")
    webbrowser.open(f"http://127.0.0.1:{PORT}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)

    print("=" * 65)
    print(f"[*] Launching Autonomous Regulatory & Tax Compliance Agent on Port {PORT}")
    print("=" * 65)

    threading.Thread(target=open_browser, daemon=True).start()

    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=PORT, reload=True)
