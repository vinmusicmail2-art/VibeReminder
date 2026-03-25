# Напоминалка - Notes and Reminders App

## Overview
A web-based notes and reminders application originally written as a Windows tkinter desktop app, converted to a Flask web application for Replit.

## Architecture
- **Backend**: Python Flask web server (`app.py`)
- **Frontend**: Single HTML page with vanilla JS (`templates/index.html`)
- **Data Storage**: JSON file (`app_data.json`) for notes and reminders
- **Voice Notes**: WebM audio files stored in `voice_notes/` directory

## Features
- **Text Notes**: Create, edit, view, and delete text notes
- **Reminders**: Schedule reminders with date/time alerts (checked every 30s in browser)
- **Voice Notes**: Record audio via browser microphone, save and play back

## Running
The app runs on port 5000 via Flask dev server.
```
python app.py
```

## Deployment
Configured for autoscale deployment with gunicorn:
```
gunicorn --bind=0.0.0.0:5000 --reuse-port app:app
```

## File Structure
```
app.py               # Flask backend with REST API
templates/
  index.html         # Single-page frontend
app_data.json        # Data storage (auto-created)
voice_notes/         # Voice recordings directory (auto-created)
reminder_app.py      # Original tkinter app (reference only)
requirements.txt     # Original dependencies (reference only)
```

## API Endpoints
- `GET /api/notes` - List all notes
- `POST /api/notes` - Save/update a note
- `DELETE /api/notes/<id>` - Delete a note
- `GET /api/reminders` - List all reminders
- `POST /api/reminders` - Add a reminder
- `DELETE /api/reminders/<id>` - Delete a reminder
- `GET /api/reminders/check` - Check for triggered reminders
- `GET /api/voice-notes` - List voice note files
- `POST /api/voice-notes/upload` - Upload a voice note
- `DELETE /api/voice-notes/<name>` - Delete a voice note
- `GET /voice_notes/<filename>` - Serve a voice note file
