"""
config.py — Application-wide constants, paths, colors, and settings.
Voice-Based Form Filling System
"""

import os

# ─────────────────────────────────────────────
# App Info
# ─────────────────────────────────────────────
APP_TITLE   = "VoiceForm AI"
APP_VERSION = "1.0.0"
APP_AUTHOR  = "DTI Project Team"
APP_DESC    = (
    "Smart Voice-Based Form Filling System\n"
    "Accessible • Intelligent • Modern"
)

# ─────────────────────────────────────────────
# Window Dimensions
# ─────────────────────────────────────────────
WIN_WIDTH  = 1100
WIN_HEIGHT = 720
WIN_MIN_W  = 900
WIN_MIN_H  = 600

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR   = os.path.join(BASE_DIR, "assets")
DB_DIR       = os.path.join(BASE_DIR, "database")
DB_PATH      = os.path.join(DB_DIR,    "form.db")
REPORTS_DIR  = os.path.join(BASE_DIR, "reports")
EXCEL_DIR    = os.path.join(REPORTS_DIR, "exported_excel")
PDF_DIR      = os.path.join(REPORTS_DIR, "exported_pdf")
LOGS_DIR     = os.path.join(BASE_DIR, "logs")
LOG_FILE     = os.path.join(LOGS_DIR, "application.log")
SCREENSHOTS  = os.path.join(BASE_DIR, "screenshots")

# Asset files
LOGO_PATH   = os.path.join(ASSETS_DIR, "logo.png")
MIC_PATH    = os.path.join(ASSETS_DIR, "microphone.png")
BG_PATH     = os.path.join(ASSETS_DIR, "background.jpg")
BANNER_PATH = os.path.join(ASSETS_DIR, "banner.jpg")
SUCCESS_PATH= os.path.join(ASSETS_DIR, "success.png")

# ─────────────────────────────────────────────
# Color Palette
# ─────────────────────────────────────────────
COLORS = {
    "primary":        "#1E88E5",   # Blue
    "primary_dark":   "#1565C0",
    "primary_light":  "#64B5F6",
    "secondary":      "#00BCD4",   # Aqua / Cyan
    "secondary_dark": "#00838F",
    "accent":         "#26C6DA",
    "bg_main":        "#F0F4F8",   # Soft gray-white
    "bg_dark":        "#1A1A2E",   # Dark mode bg
    "bg_card":        "#FFFFFF",
    "bg_card_dark":   "#16213E",
    "bg_sidebar":     "#1E3A5F",
    "text_dark":      "#1A1A2E",
    "text_medium":    "#4A5568",
    "text_light":     "#FFFFFF",
    "text_muted":     "#A0AEC0",
    "border":         "#E2E8F0",
    "success":        "#48BB78",
    "error":          "#FC8181",
    "warning":        "#F6AD55",
    "info":           "#63B3ED",
    "gradient_start": "#1E88E5",
    "gradient_end":   "#00BCD4",
}

# ─────────────────────────────────────────────
# Fonts
# ─────────────────────────────────────────────
FONT = {
    "heading1":  ("Segoe UI", 28, "bold"),
    "heading2":  ("Segoe UI", 20, "bold"),
    "heading3":  ("Segoe UI", 16, "bold"),
    "subhead":   ("Segoe UI", 13, "bold"),
    "body":      ("Segoe UI", 12),
    "body_bold": ("Segoe UI", 12, "bold"),
    "small":     ("Segoe UI", 10),
    "tiny":      ("Segoe UI", 9),
    "mono":      ("Consolas",  11),
}

# ─────────────────────────────────────────────
# Speech Recognition Settings
# ─────────────────────────────────────────────
SR_TIMEOUT       = 8     # seconds to wait for speech start
SR_PHRASE_LIMIT  = 15    # max seconds per phrase / recording length
SR_ENERGY_THRESH = 300   # mic energy threshold
SR_PAUSE_THRESH  = 1.0   # silence before phrase ends
SR_MAX_RETRIES   = 3     # retries on recognition failure
SR_RECORD_SECONDS = 8    # seconds of audio captured per listen() call
SR_SAMPLE_RATE    = 16000 # 16 kHz — optimal for speech recognition

# ─────────────────────────────────────────────
# TTS Settings
# ─────────────────────────────────────────────
TTS_RATE_DEFAULT = 165   # words per minute
TTS_VOLUME       = 1.0   # 0.0 – 1.0

# ─────────────────────────────────────────────
# Language Options
# ─────────────────────────────────────────────
LANGUAGES = {
    "English": "en-IN",
    "Hindi":   "hi-IN",
    "Telugu":  "te-IN",
}

# ─────────────────────────────────────────────
# Form Fields Definition
# ─────────────────────────────────────────────
FORM_FIELDS = [
    {
        "key":       "name",
        "label":     "Full Name",
        "question":  "Please say your full name.",
        "confirm":   "Did you say your name is {}? Please say Yes or No.",
        "icon":      "👤",
    },
    {
        "key":       "age",
        "label":     "Age",
        "question":  "Please tell me your age.",
        "confirm":   "Did you say your age is {}? Please say Yes or No.",
        "icon":      "🎂",
    },
    {
        "key":       "gender",
        "label":     "Gender",
        "question":  "Please say your gender: Male, Female, or Other.",
        "confirm":   "Did you say your gender is {}? Please say Yes or No.",
        "icon":      "⚧",
    },
    {
        "key":       "phone",
        "label":     "Mobile Number",
        "question":  "Please say your 10-digit mobile number.",
        "confirm":   "Did you say your mobile number is {}? Please say Yes or No.",
        "icon":      "📱",
    },
    {
        "key":       "email",
        "label":     "Email Address",
        "question":  "Please spell out your email address.",
        "confirm":   "Did you say your email is {}? Please say Yes or No.",
        "icon":      "📧",
    },
    {
        "key":       "address",
        "label":     "Address",
        "question":  "Please say your full home address.",
        "confirm":   "Did you say your address is {}? Please say Yes or No.",
        "icon":      "🏠",
    },
    {
        "key":       "occupation",
        "label":     "Occupation",
        "question":  "Please tell me your occupation or profession.",
        "confirm":   "Did you say your occupation is {}? Please say Yes or No.",
        "icon":      "💼",
    },
]

# ─────────────────────────────────────────────
# Theme Mode
# ─────────────────────────────────────────────
DEFAULT_THEME = "Light"   # "Light" or "Dark"

# ─────────────────────────────────────────────
# Keyboard Shortcuts
# ─────────────────────────────────────────────
SHORTCUTS = {
    "start_voice":  "<F5>",
    "manual_form":  "<F6>",
    "dashboard":    "<F7>",
    "toggle_theme": "<F8>",
    "quit":         "<Control-q>",
    "export_excel": "<Control-e>",
    "export_pdf":   "<Control-p>",
}
