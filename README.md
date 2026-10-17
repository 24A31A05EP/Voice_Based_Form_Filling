# 🎤 VoiceForm AI — Voice-Based Form Filling System

> A professional, AI-assisted desktop application that enables users to complete registration forms using voice commands. Built with Python, CustomTkinter, SpeechRecognition, and SQLite.

---

## 📌 Project Overview

**VoiceForm AI** is a smart desktop application designed to improve accessibility for elderly users, visually impaired individuals, and people with limited typing skills. Instead of typing, users simply speak their responses — the system listens, converts speech to text, validates the input, and stores it in a local SQLite database.

---

## ✨ Features

| Feature                   | Description |
|---------------------------|-------------|
| 🎙️ Voice Input            | Natural speech-to-text for all form fields |
| ✅ Smart Validation        | Real-time validation with helpful error messages |
| 🤖 Voice Confirmation      | App reads back and confirms each input |
| 📝 Manual Form             | Keyboard-based entry as an alternative |
| 📊 Dashboard               | View, search, edit, delete all records |
| 🔍 Voice Search            | Search records by speaking |
| 📄 Excel Export            | Styled .xlsx reports with openpyxl |
| 📃 PDF Export              | Professional PDF with reportlab |
| 💾 Database Backup         | One-click SQLite backup |
| 🌙 Dark / Light Mode       | Toggle with F8 or sidebar switch |
| 🌐 Multi-Language          | English, Hindi, Telugu voice support |
| ⌨️ Keyboard Shortcuts      | Quick navigation with F-keys |
| 📁 Audit Logging           | All events logged to `logs/application.log` |

---

## 🛠️ Technologies Used

| Category      | Library / Tool        |
|---------------|-----------------------|
| GUI           | CustomTkinter, Tkinter |
| Speech Input  | SpeechRecognition, PyAudio |
| Speech Output | pyttsx3              |
| Database      | SQLite3 (built-in)   |
| Data Export   | pandas, openpyxl     |
| PDF Export    | reportlab            |
| Images        | Pillow (PIL)         |
| Utilities     | threading, re, logging, datetime |

---

## 📁 Project Structure

```
Voice_Based_Form_Filling/
│
├── main.py              ← Entry point
├── gui.py               ← All screens (Home, Voice, Manual, Dashboard)
├── speech.py            ← SpeechRecognition wrapper
├── tts.py               ← pyttsx3 Text-to-Speech engine
├── database.py          ← SQLite CRUD operations
├── validation.py        ← Input validators + speech normalisers
├── export.py            ← Excel + PDF export manager
├── config.py            ← Constants, paths, theme, form fields
├── requirements.txt     ← All pip dependencies
├── README.md            ← This file
│
├── database/
│   └── form.db          ← SQLite database (auto-created)
│
├── assets/
│   ├── logo.png
│   ├── microphone.png
│   ├── banner.jpg
│   ├── success.png
│   └── background.jpg
│
├── reports/
│   ├── exported_excel/  ← .xlsx files
│   └── exported_pdf/    ← .pdf files
│
├── logs/
│   └── application.log  ← App logs
│
└── screenshots/         ← For documentation
```

---

## 🗄️ Database Schema

```sql
CREATE TABLE IF NOT EXISTS Users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    age         INTEGER NOT NULL,
    gender      TEXT    NOT NULL,
    phone       TEXT    NOT NULL,
    email       TEXT    NOT NULL,
    address     TEXT    NOT NULL,
    occupation  TEXT    NOT NULL,
    reg_date    TEXT    NOT NULL,
    reg_time    TEXT    NOT NULL
);
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.10 or higher
- Windows 10 / 11 (recommended)
- Working microphone
- Internet connection (for Google Speech Recognition)

### Step 1 — Clone / Download the Project

```bash
cd Voice_Based_Form_Filling
```

### Step 2 — Create a Virtual Environment (optional but recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note for Windows users:** If `pyaudio` fails to install, use:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

### Step 4 — Run the Application

```bash
python main.py
```

---

## 🚀 How to Use

### Voice Registration
1. Launch the app: `python main.py`
2. Click **"Start Voice Form"** from the Home screen or sidebar
3. The assistant will ask each question through the speaker
4. Speak your answer clearly into the microphone
5. Confirm with **"Yes"** or retry with **"No"**
6. After all 7 fields, click **"Submit Registration"**

### Manual Registration
1. Click **"Manual Form"** in the sidebar
2. Fill in all fields using the keyboard
3. Click **"Submit"** to save
4. Or click **"Voice Fill"** to fill fields with your voice

### Dashboard
1. Click **"Dashboard"** in the sidebar
2. View all registrations in the table
3. Use the search bar to filter records
4. Double-click a row to edit it
5. Click **"Excel"** or **"PDF"** to export reports

---

## ⌨️ Keyboard Shortcuts

| Key         | Action                |
|-------------|-----------------------|
| `F5`        | Start Voice Form      |
| `F6`        | Open Manual Form      |
| `F7`        | Open Dashboard        |
| `F8`        | Toggle Dark/Light     |
| `Ctrl+E`    | Export to Excel       |
| `Ctrl+P`    | Export to PDF         |
| `Ctrl+Q`    | Quit application      |

---

## 🔒 Error Handling

The application handles:
- No microphone detected → friendly dialog message
- Speech not recognised → retry up to 3 times
- Internet unavailable → error message (offline mode not supported for Google STT)
- Invalid form data → field-level error messages
- Database errors → logged + shown in dialog
- Missing dependencies → startup warning dialog

---

## 🌐 Multi-Language Support

Change the language from the sidebar dropdown:
- **English** (en-IN) — default
- **Hindi** (hi-IN)
- **Telugu** (te-IN)

The speech recogniser will use the selected language for all listening.

---

## 📊 Reports

Generated reports are saved automatically:
- Excel: `reports/exported_excel/VoiceForm_Report_YYYYMMDD_HHMMSS.xlsx`
- PDF:   `reports/exported_pdf/VoiceForm_Report_YYYYMMDD_HHMMSS.pdf`
- Backup: `reports/form_backup_YYYYMMDD_HHMMSS.db`

---

## 🔮 Future Enhancements

- [ ] Offline speech recognition (Vosk / Whisper)
- [ ] Face recognition for login
- [ ] Cloud database sync (Firebase / Supabase)
- [ ] Mobile companion app
- [ ] Biometric voice authentication
- [ ] OTP verification via SMS
- [ ] AI-assisted data correction
- [ ] Aadhaar / form-specific templates

---

## 👨‍💻 Authors

**DTI Project Team — B.Tech Final Year Project**

- Module: Advanced Python Programming
- Academic Year: 2025–2026

---

## 📄 License

This project is for educational purposes. All assets are royalty-free or AI-generated.
