import threading
import webbrowser
import time
import sys
import os

if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
    os.chdir(base_dir)

from app import app

def run_flask():
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()
time.sleep(1.5)

try:
    import webview
    webview.create_window('VibeNotes Pro', 'http://127.0.0.1:5000', width=480, height=850, resizable=True)
    webview.start()
except Exception:
    webbrowser.open('http://127.0.0.1:5000')
    input()
