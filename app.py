"""
VibeNotes Pro - Web version
Flask web application for reminders with voice support
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
import datetime

app = Flask(__name__)
app.secret_key = 'vibenotes-secret-key-2024'

DATA_FILE = 'app_data.json'
VOICE_NOTES_DIR = 'voice_notes'

os.makedirs(VOICE_NOTES_DIR, exist_ok=True)


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'reminders' not in data:
                    data['reminders'] = []
                return data
        except Exception:
            pass
    return {'reminders': []}


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    data = load_data()
    now = datetime.datetime.now()
    changed = False
    for r in data['reminders']:
        if r.get('status') == 'Ожидание':
            try:
                dt = datetime.datetime.strptime(r['datetime'], '%Y-%m-%d %H:%M')
                if dt <= now:
                    if r.get('repeat_daily'):
                        next_dt = dt + datetime.timedelta(days=1)
                        while next_dt <= now:
                            next_dt += datetime.timedelta(days=1)
                        r['datetime'] = next_dt.strftime('%Y-%m-%d %H:%M')
                    else:
                        r['status'] = 'Сработало'
                    changed = True
            except Exception:
                pass
    if changed:
        save_data(data)
    return jsonify(data['reminders'])


@app.route('/api/reminders', methods=['POST'])
def add_reminder():
    body = request.json
    r_type = body.get('type', 'text')
    message = body.get('message', '').strip()
    dt_str = body.get('datetime', '')
    repeat_daily = bool(body.get('repeat_daily', False))
    voice_file = body.get('voice_file', None)

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
        'voice_file': voice_file,
        'status': 'Ожидание'
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
                    if r.get('repeat_daily'):
                        next_dt = dt + datetime.timedelta(days=1)
                        while next_dt <= now:
                            next_dt += datetime.timedelta(days=1)
                        r['datetime'] = next_dt.strftime('%Y-%m-%d %H:%M')
                    else:
                        r['status'] = 'Сработало'
                    changed = True
            except Exception:
                pass
    if changed:
        save_data(data)
    return jsonify({'triggered': triggered})


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


@app.route('/voice_notes/<path:filename>')
def serve_voice_note(filename):
    return send_from_directory(VOICE_NOTES_DIR, filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
