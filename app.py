"""
VibeNotes Pro - Web version
Flask web application for reminders with voice support
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
import sys
import datetime

# When running as PyInstaller EXE, templates/static live in sys._MEIPASS,
# but user data (app_data.json, voice_notes) lives next to the EXE.
if getattr(sys, 'frozen', False):
    _BUNDLE_DIR = sys._MEIPASS
    _DATA_DIR   = os.path.dirname(sys.executable)
else:
    _BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    _DATA_DIR   = _BUNDLE_DIR

app = Flask(
    __name__,
    template_folder=os.path.join(_BUNDLE_DIR, 'templates'),
    static_folder=os.path.join(_BUNDLE_DIR, 'static'),
)
app.secret_key = 'vibenotes-secret-key-2024'

DATA_FILE     = os.path.join(_DATA_DIR, 'app_data.json')
VOICE_NOTES_DIR = os.path.join(_DATA_DIR, 'voice_notes')

os.makedirs(VOICE_NOTES_DIR, exist_ok=True)


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data.setdefault('reminders', [])
                data.setdefault('notes', [])
                return data
        except Exception:
            pass
    return {'reminders': [], 'notes': []}


def save_data(data):
    """Atomic write — protects against data corruption on crash."""
    tmp = DATA_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


def advance_reminder(r, now):
    """Advance a repeating reminder to its next future occurrence."""
    try:
        dt = datetime.datetime.strptime(r['datetime'], '%Y-%m-%d %H:%M')
        if r.get('repeat_yearly'):
            year = now.year
            try:
                next_dt = dt.replace(year=year)
            except ValueError:                          # Feb 29 in non-leap year
                next_dt = dt.replace(year=year, day=28)
            if next_dt <= now:
                try:
                    next_dt = next_dt.replace(year=year + 1)
                except ValueError:
                    next_dt = next_dt.replace(year=year + 1, day=28)
            r['datetime'] = next_dt.strftime('%Y-%m-%d %H:%M')
            return True
        elif r.get('repeat_daily'):
            next_dt = dt + datetime.timedelta(days=1)
            while next_dt <= now:
                next_dt += datetime.timedelta(days=1)
            r['datetime'] = next_dt.strftime('%Y-%m-%d %H:%M')
            return True
    except Exception:
        pass
    return False


@app.route('/')
def index():
    return render_template('index.html')


# ============================================================
# REMINDERS API
# ============================================================
@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    data = load_data()
    return jsonify(data['reminders'])


@app.route('/api/reminders', methods=['POST'])
def add_reminder():
    body = request.json
    r_type   = body.get('type', 'text')
    message  = body.get('message', '').strip()
    dt_str   = body.get('datetime', '')
    repeat_daily  = bool(body.get('repeat_daily', False))
    repeat_yearly = bool(body.get('repeat_yearly', False))
    voice_file    = body.get('voice_file', None)

    if not message:
        return jsonify({'error': 'Введите текст напоминания'}), 400
    try:
        dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
    except Exception:
        return jsonify({'error': 'Неверный формат даты/времени'}), 400
    if dt <= datetime.datetime.now():
        return jsonify({'error': 'Дата и время должны быть в будущем!'}), 400

    data = load_data()
    reminder = {
        'id': int(datetime.datetime.now().timestamp() * 1000),
        'type': r_type,
        'message': message,
        'datetime': dt_str,
        'repeat_daily': repeat_daily,
        'repeat_yearly': repeat_yearly,
        'voice_file': voice_file,
        'status': 'Ожидание',
    }
    data['reminders'].append(reminder)
    save_data(data)
    return jsonify({'success': True})


@app.route('/api/reminders/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    data = load_data()
    data['reminders'] = [r for r in data['reminders'] if r['id'] != reminder_id]
    save_data(data)
    return jsonify({'success': True})


@app.route('/api/reminders/check', methods=['GET'])
def check_reminders():
    data = load_data()
    now = datetime.datetime.now()
    triggered = []
    changed = False
    for r in data['reminders']:
        if r.get('status') == 'Ожидание':
            try:
                dt = datetime.datetime.strptime(r['datetime'], '%Y-%m-%d %H:%M')
                if dt <= now:
                    triggered.append(dict(r))
                    if r.get('repeat_yearly') or r.get('repeat_daily'):
                        if advance_reminder(r, now):
                            changed = True
                    else:
                        r['status'] = 'Сработало'
                        changed = True
            except Exception:
                pass
    if changed:
        save_data(data)
    return jsonify({'triggered': triggered})


# ============================================================
# NOTES API
# ============================================================
@app.route('/api/notes', methods=['GET'])
def get_notes():
    data = load_data()
    return jsonify(data.get('notes', []))


@app.route('/api/notes', methods=['POST'])
def save_note():
    body = request.json
    title   = body.get('title', '').strip()
    content = body.get('content', '').strip()
    reminder_datetime = body.get('reminder_datetime', None)
    reminder_repeat   = body.get('reminder_repeat', 'none') or 'none'

    if not title:
        return jsonify({'error': 'Введите заголовок'}), 400

    data    = load_data()
    note_id = int(datetime.datetime.now().timestamp() * 1000)
    note = {
        'id':      note_id,
        'title':   title,
        'content': content,
        'preview': content[:100] if content else '',
        'date':    datetime.datetime.now().strftime('%d.%m.%Y %H:%M'),
        'reminder_datetime': reminder_datetime,
        'reminder_repeat':   reminder_repeat,
    }
    data['notes'].append(note)

    if reminder_datetime:
        try:
            datetime.datetime.strptime(reminder_datetime, '%Y-%m-%d %H:%M')
            reminder = {
                'id':           note_id + 1,
                'type':         'note',
                'message':      title,
                'note_content': content,
                'note_id':      note_id,
                'datetime':     reminder_datetime,
                'repeat_daily':  reminder_repeat == 'daily',
                'repeat_yearly': reminder_repeat == 'yearly',
                'voice_file':   None,
                'status':       'Ожидание',
            }
            data['reminders'].append(reminder)
        except Exception:
            pass

    save_data(data)
    return jsonify({'success': True})


@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    data = load_data()
    data['notes']     = [n for n in data.get('notes', [])     if n['id'] != note_id]
    data['reminders'] = [r for r in data.get('reminders', []) if r.get('note_id') != note_id]
    save_data(data)
    return jsonify({'success': True})


# ============================================================
# VOICE NOTES API
# ============================================================
@app.route('/api/voice-notes/upload', methods=['POST'])
def upload_voice_note():
    if 'file' not in request.files:
        return jsonify({'error': 'Нет файла'}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'error': 'Пустое имя файла'}), 400
    safe_name = os.path.basename(f.filename)
    fpath = os.path.join(VOICE_NOTES_DIR, safe_name)
    f.save(fpath)
    return jsonify({'success': True, 'filename': safe_name})


@app.route('/api/voice-notes', methods=['GET'])
def list_voice_notes():
    """Returns list of {name, date} objects — date from file mtime."""
    files = []
    if os.path.exists(VOICE_NOTES_DIR):
        for fname in sorted(os.listdir(VOICE_NOTES_DIR)):
            if fname.endswith(('.webm', '.wav', '.mp3')):
                fpath = os.path.join(VOICE_NOTES_DIR, fname)
                mtime = os.path.getmtime(fpath)
                date_str = datetime.datetime.fromtimestamp(mtime).strftime('%d.%m.%Y %H:%M')
                files.append({'name': fname, 'date': date_str})
    return jsonify(files)


@app.route('/api/voice-notes/<path:filename>', methods=['DELETE'])
def delete_voice_note(filename):
    safe_name = os.path.basename(filename)
    fpath = os.path.join(VOICE_NOTES_DIR, safe_name)
    if os.path.exists(fpath):
        os.remove(fpath)
    return jsonify({'success': True})


@app.route('/voice_notes/<path:filename>')
def serve_voice_note(filename):
    return send_from_directory(VOICE_NOTES_DIR, filename)


@app.route('/manifest.json')
def manifest():
    return send_from_directory(app.static_folder, 'manifest.json')


@app.route('/sw.js')
def service_worker():
    response = send_from_directory(app.static_folder, 'sw.js')
    response.headers['Service-Worker-Allowed'] = '/'
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
