# VibeNotes Pro — Десктопное приложение для Windows

## Описание
Настольное приложение для заметок и напоминаний с поддержкой голосовых записей.
**Предназначено исключительно для Windows 10/11.**

## Архитектура
- **Точка входа**: `launcher.py` — запускает Flask внутри + открывает окно pywebview + системный трей (pystray)
- **Бэкенд**: `app.py` — Flask REST API (не запускается напрямую, используется launcher)
- **Интерфейс**: `templates/index.html` — отображается в pywebview окне
- **Хранение данных**: `app_data.json` — заметки и напоминания (JSON)
- **Голосовые записи**: папка `voice_notes/` — файлы `.webm`

## Как собрать .exe

### 1. Установить зависимости
```
pip install flask pywebview pystray Pillow pygame pyinstaller
```

### 2. Собрать исполняемый файл
```
pyinstaller VibeNotes.spec
```

Готовый `.exe` появится в папке `dist/`.

## Запуск без сборки (в режиме разработки, Windows)
```
python launcher.py
```

## Структура файлов
```
launcher.py          # Точка входа (десктоп: Flask + pywebview + трей)
app.py               # Flask REST API (библиотека, не запускать напрямую)
templates/
  index.html         # Интерфейс приложения
static/
  icon-192.png       # Иконка приложения
  icon-512.png       # Иконка приложения (большая)
app_data.json        # База данных (создаётся автоматически)
voice_notes/         # Папка для голосовых записей (создаётся автоматически)
VibeNotes.spec       # Конфигурация PyInstaller для сборки .exe
requirements.txt     # Зависимости Python
```

## API (внутренний Flask, используется интерфейсом)
- `GET /api/notes` — список заметок
- `POST /api/notes` — сохранить заметку
- `DELETE /api/notes/<id>` — удалить заметку
- `GET /api/reminders` — список напоминаний
- `POST /api/reminders` — добавить напоминание
- `DELETE /api/reminders/<id>` — удалить напоминание
- `GET /api/reminders/check` — проверить сработавшие напоминания
- `GET /api/voice-notes` — список голосовых записей
- `POST /api/voice-notes/upload` — загрузить голосовую запись
- `DELETE /api/voice-notes/<name>` — удалить голосовую запись
- `GET /voice_notes/<filename>` — воспроизвести голосовую запись

## Особенности десктопной версии
- Окно закрывается в системный трей (не завершает приложение)
- Автозапуск при входе в Windows (при запуске как .exe)
- Уведомления проверяются каждые 30 секунд
- Голосовые напоминания воспроизводятся в окне уведомления
