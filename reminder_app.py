--- reminder_app.py (原始)


+++ reminder_app.py (修改后)
"""
Приложение-напоминалка для Windows 10
Функции: блокнот, заметки, текстовые и голосовые напоминания
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import os
import datetime
import threading
import time
import wave
import pyaudio
import pygame
from pathlib import Path
import pickle

class VoiceRecorder:
    """Класс для записи голоса"""

    def __init__(self):
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.frames = []
        self.is_recording = False
        self.audio = None
        self.stream = None

    def start_recording(self):
        """Начать запись"""
        try:
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            self.frames = []
            self.is_recording = True

            def record():
                while self.is_recording:
                    data = self.stream.read(self.chunk)
                    self.frames.append(data)

            self.thread = threading.Thread(target=record)
            self.thread.start()
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось начать запись: {str(e)}")
            return False

    def stop_recording(self, filename):
        """Остановить запись и сохранить файл"""
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()

        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.frames))
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить запись: {str(e)}")
            return False


class ReminderApp:
    """Основное приложение напоминалки"""

    def __init__(self, root):
        self.root = root
        self.root.title("Напоминалка - Блокнот и Напоминания")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Инициализация pygame для звука
        pygame.mixer.init()

        # Данные приложения
        self.notes = []
        self.reminders = []
        self.voice_recorder = VoiceRecorder()
        self.recording = False
        self.current_recording_file = None

        # Загрузка данных
        self.load_data()

        # Создание интерфейса
        self.create_menu()
        self.create_main_interface()

        # Запуск проверки напоминаний
        self.check_reminders_loop()

        # Сохранение при закрытии
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_menu(self):
        """Создание меню приложения"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Новая заметка", command=self.new_note)
        file_menu.add_command(label="Открыть заметку", command=self.open_note)
        file_menu.add_command(label="Сохранить заметку", command=self.save_note)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.on_closing)

        # Напоминания
        reminder_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Напоминания", menu=reminder_menu)
        reminder_menu.add_command(label="Добавить напоминание", command=self.add_reminder_dialog)
        reminder_menu.add_command(label="Управление напоминаниями", command=self.show_reminders_window)

        # Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)

    def create_main_interface(self):
        """Создание основного интерфейса"""
        # Главный контейнер с вкладками
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Создание вкладок
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Вкладка заметок
        self.notes_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.notes_frame, text="📝 Заметки")
        self.create_notes_tab()

        # Вкладка напоминаний
        self.reminders_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reminders_frame, text="⏰ Напоминания")
        self.create_reminders_tab()

        # Вкладка голосовых заметок
        self.voice_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.voice_frame, text="🎤 Голосовые заметки")
        self.create_voice_tab()

    def create_notes_tab(self):
        """Создание вкладки заметок"""
        # Панель инструментов
        toolbar = ttk.Frame(self.notes_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(toolbar, text="➕ Новая", command=self.new_note).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 Сохранить", command=self.save_note).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📂 Открыть", command=self.open_note).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Удалить", command=self.delete_note).pack(side=tk.LEFT, padx=2)

        # Список заметок
        list_frame = ttk.LabelFrame(self.notes_frame, text="Список заметок")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Создаем Treeview для списка заметок
        columns = ('title', 'date', 'preview')
        self.notes_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        self.notes_tree.heading('title', text='Заголовок')
        self.notes_tree.heading('date', text='Дата изменения')
        self.notes_tree.heading('preview', text='Предпросмотр')

        self.notes_tree.column('title', width=200)
        self.notes_tree.column('date', width=150)
        self.notes_tree.column('preview', width=400)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.notes_tree.yview)
        self.notes_tree.configure(yscrollcommand=scrollbar.set)

        self.notes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Привязка двойного клика
        self.notes_tree.bind('<Double-1>', self.open_selected_note)

        # Поле редактирования
        edit_frame = ttk.LabelFrame(self.notes_frame, text="Редактор заметки")
        edit_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.note_title = ttk.Entry(edit_frame, font=('Arial', 12))
        self.note_title.pack(fill=tk.X, pady=(0, 5))
        self.note_title.insert(0, "Заголовок заметки")

        self.note_text = tk.Text(edit_frame, font=('Arial', 11), wrap=tk.WORD)
        self.note_text.pack(fill=tk.BOTH, expand=True)

        # Заполняем список заметок
        self.refresh_notes_list()

    def create_reminders_tab(self):
        """Создание вкладки напоминаний"""
        # Кнопки управления
        btn_frame = ttk.Frame(self.reminders_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="➕ Добавить напоминание",
                  command=self.add_reminder_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Обновить",
                  command=self.refresh_reminders_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Удалить выбранное",
                  command=self.delete_reminder).pack(side=tk.LEFT, padx=5)

        # Список напоминаний
        list_frame = ttk.LabelFrame(self.reminders_frame, text="Активные напоминания")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        columns = ('type', 'message', 'datetime', 'status')
        self.reminders_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        self.reminders_tree.heading('type', text='Тип')
        self.reminders_tree.heading('message', text='Сообщение')
        self.reminders_tree.heading('datetime', text='Дата и время')
        self.reminders_tree.heading('status', text='Статус')

        self.reminders_tree.column('type', width=80)
        self.reminders_tree.column('message', width=300)
        self.reminders_tree.column('datetime', width=150)
        self.reminders_tree.column('status', width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.reminders_tree.yview)
        self.reminders_tree.configure(yscrollcommand=scrollbar.set)

        self.reminders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.refresh_reminders_list()

    def create_voice_tab(self):
        """Создание вкладки голосовых заметок"""
        # Информация
        info_label = ttk.Label(self.voice_frame,
                              text="Запишите голосовую заметку или голосовое напоминание",
                              font=('Arial', 11))
        info_label.pack(pady=10)

        # Кнопки управления записью
        btn_frame = ttk.Frame(self.voice_frame)
        btn_frame.pack(pady=20)

        self.record_btn = ttk.Button(btn_frame, text="🔴 Начать запись",
                                     command=self.toggle_recording)
        self.record_btn.pack(side=tk.LEFT, padx=10)

        ttk.Button(btn_frame, text="💾 Сохранить как заметку",
                  command=self.save_voice_as_note).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="⏰ Установить как напоминание",
                  command=self.set_voice_reminder).pack(side=tk.LEFT, padx=10)

        # Статус записи
        self.status_label = ttk.Label(self.voice_frame, text="Готов к записи",
                                      font=('Arial', 10), foreground='green')
        self.status_label.pack(pady=10)

        # Список голосовых заметок
        list_frame = ttk.LabelFrame(self.voice_frame, text="Голосовые заметки")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=20)

        columns = ('name', 'date', 'duration')
        self.voice_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        self.voice_tree.heading('name', text='Название')
        self.voice_tree.heading('date', text='Дата создания')
        self.voice_tree.heading('duration', text='Длительность')

        self.voice_tree.column('name', width=300)
        self.voice_tree.column('date', width=150)
        self.voice_tree.column('duration', width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.voice_tree.yview)
        self.voice_tree.configure(yscrollcommand=scrollbar.set)

        self.voice_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Кнопки воспроизведения
        play_frame = ttk.Frame(self.voice_frame)
        play_frame.pack(pady=10)

        ttk.Button(play_frame, text="▶️ Воспроизвести",
                  command=self.play_voice).pack(side=tk.LEFT, padx=5)
        ttk.Button(play_frame, text="🗑️ Удалить",
                  command=self.delete_voice).pack(side=tk.LEFT, padx=5)

        self.refresh_voice_list()

    def new_note(self):
        """Создание новой заметки"""
        self.note_title.delete(0, tk.END)
        self.note_title.insert(0, "Новая заметка")
        self.note_text.delete(1.0, tk.END)
        self.note_text.focus()

    def save_note(self):
        """Сохранение заметки"""
        title = self.note_title.get().strip()
        content = self.note_text.get(1.0, tk.END).strip()

        if not title or not content:
            messagebox.showwarning("Предупреждение", "Введите заголовок и содержание заметки")
            return

        # Добавляем в список заметок
        note = {
            'id': len(self.notes) + 1,
            'title': title,
            'content': content,
            'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            'preview': content[:50] + "..." if len(content) > 50 else content
        }

        # Проверяем, существует ли уже заметка с таким заголовком
        existing = next((n for n in self.notes if n['title'] == title), None)
        if existing:
            existing.update(note)
        else:
            self.notes.append(note)

        self.save_data()
        self.refresh_notes_list()
        messagebox.showinfo("Успех", "Заметка сохранена!")

    def open_note(self):
        """Открытие заметки из файла"""
        filepath = filedialog.askopenfilename(
            title="Открыть заметку",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                self.note_title.delete(0, tk.END)
                self.note_title.insert(0, os.path.basename(filepath))
                self.note_text.delete(1.0, tk.END)
                self.note_text.insert(1.0, content)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл: {str(e)}")

    def open_selected_note(self, event=None):
        """Открытие выбранной заметки из списка"""
        selected = self.notes_tree.selection()
        if not selected:
            return

        item = self.notes_tree.item(selected[0])
        title = item['values'][0]

        note = next((n for n in self.notes if n['title'] == title), None)
        if note:
            self.note_title.delete(0, tk.END)
            self.note_title.insert(0, note['title'])
            self.note_text.delete(1.0, tk.END)
            self.note_text.insert(1.0, note['content'])

    def delete_note(self):
        """Удаление выбранной заметки"""
        selected = self.notes_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите заметку для удаления")
            return

        if messagebox.askyesno("Подтверждение", "Удалить выбранную заметку?"):
            item = self.notes_tree.item(selected[0])
            title = item['values'][0]
            self.notes = [n for n in self.notes if n['title'] != title]
            self.save_data()
            self.refresh_notes_list()

    def refresh_notes_list(self):
        """Обновление списка заметок"""
        for item in self.notes_tree.get_children():
            self.notes_tree.delete(item)

        for note in self.notes:
            self.notes_tree.insert('', tk.END, values=(
                note['title'],
                note['date'],
                note['preview']
            ))

    def add_reminder_dialog(self):
        """Диалог добавления напоминания"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить напоминание")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Тип напоминания:", font=('Arial', 11)).pack(pady=5)

        reminder_type = tk.StringVar(value="text")
        type_frame = ttk.Frame(dialog)
        type_frame.pack(pady=5)
        ttk.Radiobutton(type_frame, text="Текстовое", variable=reminder_type,
                       value="text").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(type_frame, text="Голосовое", variable=reminder_type,
                       value="voice").pack(side=tk.LEFT, padx=10)

        ttk.Label(dialog, text="Сообщение:", font=('Arial', 11)).pack(pady=5)
        message_entry = ttk.Entry(dialog, width=50, font=('Arial', 11))
        message_entry.pack(pady=5)

        ttk.Label(dialog, text="Или выберите голосовой файл:", font=('Arial', 11)).pack(pady=5)
        voice_file_var = tk.StringVar()
        voice_entry = ttk.Entry(dialog, textvariable=voice_file_var, width=40)
        voice_entry.pack(pady=5)

        def browse_voice():
            filepath = filedialog.askopenfilename(
                filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
            )
            if filepath:
                voice_file_var.set(filepath)

        ttk.Button(dialog, text="Обзор...", command=browse_voice).pack(pady=5)

        ttk.Label(dialog, text="Дата и время:", font=('Arial', 11)).pack(pady=5)

        # Дата
        date_frame = ttk.Frame(dialog)
        date_frame.pack(pady=5)

        now = datetime.datetime.now()
        year_var = tk.StringVar(value=str(now.year))
        month_var = tk.StringVar(value=str(now.month).zfill(2))
        day_var = tk.StringVar(value=str(now.day).zfill(2))
        hour_var = tk.StringVar(value=str(now.hour).zfill(2))
        minute_var = tk.StringVar(value=str(now.minute).zfill(2))

        ttk.Label(date_frame, text="Год:").pack(side=tk.LEFT)
        ttk.Entry(date_frame, textvariable=year_var, width=6).pack(side=tk.LEFT, padx=5)
        ttk.Label(date_frame, text="Месяц:").pack(side=tk.LEFT)
        ttk.Entry(date_frame, textvariable=month_var, width=4).pack(side=tk.LEFT, padx=5)
        ttk.Label(date_frame, text="День:").pack(side=tk.LEFT)
        ttk.Entry(date_frame, textvariable=day_var, width=4).pack(side=tk.LEFT, padx=5)
        ttk.Label(date_frame, text="Час:").pack(side=tk.LEFT)
        ttk.Entry(date_frame, textvariable=hour_var, width=4).pack(side=tk.LEFT, padx=5)
        ttk.Label(date_frame, text="Мин:").pack(side=tk.LEFT)
        ttk.Entry(date_frame, textvariable=minute_var, width=4).pack(side=tk.LEFT, padx=5)

        def save_reminder():
            try:
                dt = datetime.datetime(
                    int(year_var.get()),
                    int(month_var.get()),
                    int(day_var.get()),
                    int(hour_var.get()),
                    int(minute_var.get())
                )

                if dt <= datetime.datetime.now():
                    messagebox.showwarning("Предупреждение",
                                         "Дата должна быть в будущем!")
                    return

                r_type = reminder_type.get()
                if r_type == "text":
                    message = message_entry.get().strip()
                    if not message:
                        messagebox.showwarning("Предупреждение", "Введите текст напоминания")
                        return
                    voice_file = None
                else:
                    voice_file = voice_file_var.get().strip()
                    if not voice_file or not os.path.exists(voice_file):
                        messagebox.showwarning("Предупреждение",
                                             "Укажите существующий голосовой файл")
                        return
                    message = f"🎤 Голосовое: {os.path.basename(voice_file)}"

                reminder = {
                    'id': len(self.reminders) + 1,
                    'type': 'voice' if voice_file else 'text',
                    'message': message,
                    'datetime': dt.strftime("%Y-%m-%d %H:%M"),
                    'datetime_obj': dt,
                    'voice_file': voice_file,
                    'status': 'Ожидание'
                }

                self.reminders.append(reminder)
                self.save_data()
                self.refresh_reminders_list()
                messagebox.showinfo("Успех", "Напоминание добавлено!")
                dialog.destroy()

            except ValueError as e:
                messagebox.showerror("Ошибка", f"Неверный формат даты/времени: {str(e)}")

        ttk.Button(dialog, text="Сохранить", command=save_reminder).pack(pady=20)

    def refresh_reminders_list(self):
        """Обновление списка напоминаний"""
        for item in self.reminders_tree.get_children():
            self.reminders_tree.delete(item)

        for reminder in sorted(self.reminders, key=lambda x: x['datetime_obj']):
            self.reminders_tree.insert('', tk.END, values=(
                '🎤' if reminder['type'] == 'voice' else '📝',
                reminder['message'],
                reminder['datetime'],
                reminder['status']
            ))

    def delete_reminder(self):
        """Удаление напоминания"""
        selected = self.reminders_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите напоминание для удаления")
            return

        if messagebox.askyesno("Подтверждение", "Удалить выбранное напоминание?"):
            item = self.reminders_tree.item(selected[0])
            msg = item['values'][1]
            self.reminders = [r for r in self.reminders if r['message'] != msg]
            self.save_data()
            self.refresh_reminders_list()

    def toggle_recording(self):
        """Переключение записи голоса"""
        if not self.recording:
            # Начало записи
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_recording_file = f"voice_notes/recording_{timestamp}.wav"

            # Создаем директорию если нет
            os.makedirs("voice_notes", exist_ok=True)

            if self.voice_recorder.start_recording():
                self.recording = True
                self.record_btn.config(text="⏹️ Остановить запись")
                self.status_label.config(text="🔴 Запись идет...", foreground='red')
        else:
            # Остановка записи
            self.voice_recorder.stop_recording(self.current_recording_file)
            self.recording = False
            self.record_btn.config(text="🔴 Начать запись")
            self.status_label.config(text="✅ Запись сохранена", foreground='green')
            self.refresh_voice_list()

    def save_voice_as_note(self):
        """Сохранение голосовой заметки как текстовой"""
        selected = self.voice_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите голосовую заметку")
            return

        item = self.voice_tree.item(selected[0])
        filename = item['values'][0]

        self.note_title.delete(0, tk.END)
        self.note_title.insert(0, f"Голосовая заметка: {filename}")
        self.note_text.delete(1.0, tk.END)
        self.note_text.insert(1.0, f"Аудиофайл: voice_notes/{filename}\n\n"
                                   "Это голосовая заметка. Прослушайте её через вкладку 'Голосовые заметки'.")

    def set_voice_reminder(self):
        """Установка голосовой заметки как напоминания"""
        selected = self.voice_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите голосовую заметку")
            return

        item = self.voice_tree.item(selected[0])
        filename = item['values'][0]
        filepath = f"voice_notes/{filename}"

        if not os.path.exists(filepath):
            messagebox.showerror("Ошибка", "Файл не найден!")
            return

        # Диалог выбора даты
        date_str = simpledialog.askstring(
            "Дата напоминания",
            "Введите дату и время (ГГГГ-ММ-ДД ЧЧ:ММ):\nПример: 2025-01-15 14:30",
            initialvalue=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        )

        if date_str:
            try:
                dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                if dt <= datetime.datetime.now():
                    messagebox.showwarning("Предупреждение", "Дата должна быть в будущем!")
                    return

                reminder = {
                    'id': len(self.reminders) + 1,
                    'type': 'voice',
                    'message': f"🎤 Голосовое: {filename}",
                    'datetime': dt.strftime("%Y-%m-%d %H:%M"),
                    'datetime_obj': dt,
                    'voice_file': filepath,
                    'status': 'Ожидание'
                }

                self.reminders.append(reminder)
                self.save_data()
                self.refresh_reminders_list()
                messagebox.showinfo("Успех", "Голосовое напоминание установлено!")

            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат даты!")

    def refresh_voice_list(self):
        """Обновление списка голосовых заметок"""
        for item in self.voice_tree.get_children():
            self.voice_tree.delete(item)

        voice_dir = Path("voice_notes")
        if voice_dir.exists():
            for wav_file in voice_dir.glob("*.wav"):
                stat = wav_file.stat()
                date_created = datetime.datetime.fromtimestamp(stat.st_ctime)

                # Примерная длительность (можно улучшить)
                try:
                    with wave.open(str(wav_file), 'rb') as wf:
                        frames = wf.getnframes()
                        rate = wf.getframerate()
                        duration = frames / float(rate)
                        duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}"
                except:
                    duration_str = "N/A"

                self.voice_tree.insert('', tk.END, values=(
                    wav_file.name,
                    date_created.strftime("%Y-%m-%d %H:%M"),
                    duration_str
                ))

    def play_voice(self):
        """Воспроизведение выбранной голосовой заметки"""
        selected = self.voice_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите голосовую заметку")
            return

        item = self.voice_tree.item(selected[0])
        filename = item['values'][0]
        filepath = f"voice_notes/{filename}"

        if not os.path.exists(filepath):
            messagebox.showerror("Ошибка", "Файл не найден!")
            return

        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось воспроизвести: {str(e)}")

    def delete_voice(self):
        """Удаление голосовой заметки"""
        selected = self.voice_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите голосовую заметку")
            return

        if messagebox.askyesno("Подтверждение", "Удалить выбранную голосовую заметку?"):
            item = self.voice_tree.item(selected[0])
            filename = item['values'][0]
            filepath = f"voice_notes/{filename}"

            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                self.refresh_voice_list()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить: {str(e)}")

    def check_reminders_loop(self):
        """Циклическая проверка напоминаний"""
        now = datetime.datetime.now()

        for reminder in self.reminders:
            if reminder['status'] == 'Ожидание':
                if now >= reminder['datetime_obj']:
                    self.trigger_reminder(reminder)
                    reminder['status'] = 'Выполнено'
                    self.save_data()
                    self.refresh_reminders_list()

        # Проверка каждые 5 секунд
        self.root.after(5000, self.check_reminders_loop)

    def trigger_reminder(self, reminder):
        """Активация напоминания"""
        # Создание всплывающего окна
        alert_window = tk.Toplevel(self.root)
        alert_window.title("⚠️ НАПОМИНАНИЕ!")
        alert_window.geometry("500x300")
        alert_window.attributes('-topmost', True)

        # Делаем окно модальным
        alert_window.transient(self.root)
        alert_window.grab_set()

        # Стиль окна
        alert_window.configure(bg='yellow')

        # Заголовок
        title_label = tk.Label(
            alert_window,
            text="🔔 НАПОМИНАНИЕ!",
            font=('Arial', 20, 'bold'),
            bg='yellow',
            fg='red'
        )
        title_label.pack(pady=20)

        # Сообщение
        msg_label = tk.Label(
            alert_window,
            text=reminder['message'],
            font=('Arial', 14),
            bg='yellow',
            wraplength=450
        )
        msg_label.pack(pady=10)

        # Дата
        date_label = tk.Label(
            alert_window,
            text=f"Время: {reminder['datetime']}",
            font=('Arial', 11),
            bg='yellow'
        )
        date_label.pack(pady=5)

        # Кнопка ОК
        ok_btn = tk.Button(
            alert_window,
            text="✓ Понятно",
            font=('Arial', 12, 'bold'),
            bg='green',
            fg='white',
            command=alert_window.destroy,
            width=15,
            height=2
        )
        ok_btn.pack(pady=20)

        # Воспроизведение звука
        self.play_alert_sound()

        # Если голосовое напоминание
        if reminder['type'] == 'voice' and reminder.get('voice_file'):
            if os.path.exists(reminder['voice_file']):
                try:
                    pygame.mixer.music.load(reminder['voice_file'])
                    pygame.mixer.music.play()
                except:
                    pass

        # Мигание окна
        def blink():
            if alert_window.winfo_exists():
                current_bg = alert_window.cget('bg')
                new_bg = 'red' if current_bg == 'yellow' else 'yellow'
                alert_window.configure(bg=new_bg)
                title_label.configure(bg=new_bg)
                msg_label.configure(bg=new_bg)
                date_label.configure(bg=new_bg)
                alert_window.after(500, blink)

        blink()

    def play_alert_sound(self):
        """Воспроизведение звука оповещения"""
        try:
            # Простой звуковой сигнал
            alert_sound = Path("alert_sound.wav")

            # Если нет файла, создаем простой звук
            if not alert_sound.exists():
                self.create_simple_beep(alert_sound)

            pygame.mixer.music.load(str(alert_sound))
            pygame.mixer.music.play()
        except Exception as e:
            # Резервный вариант - системный звук
            try:
                import winsound
                winsound.Beep(1000, 500)
            except:
                print(f"Sound error: {e}")

    def create_simple_beep(self, filepath):
        """Создание простого звукового файла"""
        try:
            import numpy as np

            # Параметры
            duration = 0.5  # секунды
            frequency = 1000  # Гц
            sample_rate = 44100

            # Генерация синусоиды
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)

            # Сохранение в WAV
            with wave.open(str(filepath), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())
        except:
            pass

    def show_reminders_window(self):
        """Показать окно управления напоминаниями"""
        self.notebook.select(1)  # Переключиться на вкладку напоминаний

    def show_about(self):
        """Показать информацию о программе"""
        messagebox.showinfo(
            "О программе",
            "Напоминалка v1.0\n\n"
            "Приложение для создания заметок и напоминаний\n"
            "с поддержкой текста и голоса.\n\n"
            "Функции:\n"
            "• Текстовые заметки\n"
            "• Голосовые заметки\n"
            "• Напоминания с датой и временем\n"
            "• Звуковое оповещение\n"
            "• Всплывающие окна"
        )

    def load_data(self):
        """Загрузка данных из файла"""
        try:
            if os.path.exists("app_data.json"):
                with open("app_data.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.notes = data.get('notes', [])

                    # Восстанавливаем datetime объекты
                    reminders_raw = data.get('reminders', [])
                    for r in reminders_raw:
                        r['datetime_obj'] = datetime.datetime.strptime(
                            r['datetime'], "%Y-%m-%d %H:%M"
                        )
                    self.reminders = reminders_raw
        except Exception as e:
            print(f"Error loading  {e}")
            self.notes = []
            self.reminders = []

    def save_data(self):
        """Сохранение данных в файл"""
        try:
            # Сериализуем данные (без datetime объектов)
            data = {
                'notes': self.notes,
                'reminders': [{
                    'id': r['id'],
                    'type': r['type'],
                    'message': r['message'],
                    'datetime': r['datetime'],
                    'voice_file': r.get('voice_file'),
                    'status': r['status']
                } for r in self.reminders]
            }

            with open("app_data.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные: {str(e)}")

    def on_closing(self):
        """Обработка закрытия приложения"""
        if messagebox.askokcancel("Выход", "Вы действительно хотите выйти?"):
            self.save_data()
            pygame.mixer.quit()
            self.root.destroy()


def main():
    """Точка входа приложения"""
    root = tk.Tk()

    # Установка иконки (если есть)
    try:
        root.iconbitmap("icon.ico")
    except:
        pass

    app = ReminderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()