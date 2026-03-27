"""
VibeNotes Pro — Desktop launcher
- Starts Flask in a background thread
- Opens a native window via pywebview
- Adds a system-tray icon (pystray) so the app lives in the tray when minimised
- Registers itself in Windows autostart (only when running as compiled .exe)
- Closing the window hides it to tray; Exit from tray menu quits completely
"""

import threading
import time
import sys
import os
import urllib.request

# ── Path setup ────────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    # Running as PyInstaller .exe
    _BASE = sys._MEIPASS          # bundled files (templates, static, …)
    _EXE  = sys.executable        # full path to the .exe
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))
    _EXE  = None

os.chdir(_BASE)

# ── Start Flask ───────────────────────────────────────────────────────────────
from app import app as flask_app

def _run_flask():
    flask_app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

threading.Thread(target=_run_flask, daemon=True).start()

# Wait until Flask is ready (up to 10 s)
for _ in range(40):
    try:
        urllib.request.urlopen('http://127.0.0.1:5000', timeout=0.5)
        break
    except Exception:
        time.sleep(0.25)

# ── Windows autostart (EXE only) ──────────────────────────────────────────────
def _register_autostart():
    if _EXE is None:
        return
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Run',
            0, winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, 'VibeNotes Pro', 0, winreg.REG_SZ, f'"{_EXE}"')
        winreg.CloseKey(key)
    except Exception:
        pass

_register_autostart()

# ── Tray icon image (drawn with Pillow, no external file needed) ───────────────
def _make_icon_image():
    from PIL import Image, ImageDraw
    size = 64
    img  = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d    = ImageDraw.Draw(img)
    # Blue circle background
    d.ellipse([2, 2, size - 2, size - 2], fill=(173, 198, 255, 255))
    # Three dark lines representing a note
    lx1, lx2 = 18, 46
    for cy in [22, 32, 42]:
        d.rectangle([lx1, cy - 3, lx2 if cy != 42 else 36, cy + 3],
                    fill=(0, 26, 65, 255))
    return img

# ── Main: tray + webview ───────────────────────────────────────────────────────
try:
    import webview
    import pystray

    _window = None

    def _show(icon, item):
        if _window:
            _window.show()

    def _hide(icon, item):
        if _window:
            _window.hide()

    def _quit(icon, item):
        icon.stop()
        os._exit(0)

    _menu = pystray.Menu(
        pystray.MenuItem('Открыть VibeNotes', _show, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Выход', _quit),
    )

    _tray = pystray.Icon('VibeNotes Pro', _make_icon_image(), 'VibeNotes Pro', _menu)
    _tray.run_detached()   # tray runs in its own thread

    _window = webview.create_window(
        'VibeNotes Pro',
        'http://127.0.0.1:5000',
        width=480,
        height=850,
        resizable=True,
    )

    # Intercept the close button → hide to tray instead of quitting
    def _on_closing():
        _window.hide()
        return False   # cancel the actual close

    _window.events.closing += _on_closing

    webview.start()   # blocks until webview exits (only via tray → Выход)
    _tray.stop()

except ImportError as e:
    # Missing dependency — tell the user exactly what to install
    print(f'\n[!] Не установлена библиотека: {e}')
    print('    Выполни в командной строке:')
    print('    pip install pywebview pystray pillow\n')
    import webbrowser
    webbrowser.open('http://127.0.0.1:5000')
    input('Приложение открыто в браузере. Нажми Enter для выхода...')

except Exception as e:
    print(f'\n[!] Ошибка запуска: {e}')
    import webbrowser
    webbrowser.open('http://127.0.0.1:5000')
    input('Приложение открыто в браузере. Нажми Enter для выхода...')
