"""
gui.py — Complete CustomTkinter GUI for the Voice Form Filling System.

Screens:
  1. HomeScreen      — Landing page with navigation buttons
  2. VoiceFormScreen — Guided voice registration with animated mic
  3. ManualFormScreen— Keyboard-based registration form
  4. DashboardScreen — Record table, search, edit, delete, export
"""

import os
import threading
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw

from config import (
    APP_TITLE, APP_VERSION, APP_DESC,
    WIN_WIDTH, WIN_HEIGHT, WIN_MIN_W, WIN_MIN_H,
    COLORS, FONT, FORM_FIELDS, LANGUAGES,
    LOGO_PATH, MIC_PATH, BANNER_PATH, SUCCESS_PATH, BG_PATH,
    SHORTCUTS, DEFAULT_THEME,
)
from database   import DatabaseManager
from validation import Validator
from speech     import SpeechEngine, MicrophoneNotFoundError, SpeechRecognitionError
from tts        import TTSEngine
from export     import ExportManager

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Shared utilities
# ═══════════════════════════════════════════════════════════════
def load_ctk_image(path: str, size: tuple[int, int]) -> ctk.CTkImage | None:
    """Safely load an image as a CTkImage; returns None on error."""
    try:
        if os.path.exists(path):
            img = Image.open(path).convert("RGBA")
            return ctk.CTkImage(img, size=size)
    except Exception as exc:
        logger.warning("load_ctk_image failed for %s: %s", path, exc)
    return None


def create_placeholder_image(size: tuple[int, int], color: str, text: str = "") -> ctk.CTkImage:
    """Generate a solid-color placeholder CTkImage."""
    img = Image.new("RGBA", size, color)
    if text:
        from PIL import ImageFont
        draw = ImageDraw.Draw(img)
        draw.text((size[0]//2, size[1]//2), text, fill="white", anchor="mm")
    return ctk.CTkImage(img, size=size)


# ═══════════════════════════════════════════════════════════════
#  Main Application
# ═══════════════════════════════════════════════════════════════
class Application(ctk.CTk):
    """Root application window managing screen navigation and shared services."""

    def __init__(self):
        super().__init__()

        # ── Services
        self.db         = DatabaseManager()
        self.validator  = Validator()
        self.tts        = TTSEngine()
        self.speech     = SpeechEngine()
        self.exporter   = ExportManager()

        # ── State
        self._theme     = DEFAULT_THEME
        self._language  = "English"
        self._current_screen: ctk.CTkFrame | None = None
        self._screens: dict[str, ctk.CTkFrame]    = {}

        # ── Window config
        self._configure_window()
        self._apply_theme(DEFAULT_THEME)
        self._build_sidebar()
        self._build_content_area()

        # ── Bind shortcuts
        self._bind_shortcuts()

        # ── Show home
        self.show_screen("home")

        # ── TTS welcome (in thread)
        threading.Thread(target=self.tts.welcome, daemon=True).start()

        logger.info("Application started.")

    # ─────────────────────────────────────────
    # Window
    # ─────────────────────────────────────────
    def _configure_window(self):
        self.title(f"{APP_TITLE}  v{APP_VERSION}")
        self.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
        self.minsize(WIN_MIN_W, WIN_MIN_H)
        self.configure(fg_color=COLORS["bg_main"])
        # Centre on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - WIN_WIDTH)  // 2
        y  = (sh - WIN_HEIGHT) // 2
        self.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}+{x}+{y}")

    # ─────────────────────────────────────────
    # Theme
    # ─────────────────────────────────────────
    def _apply_theme(self, mode: str):
        self._theme = mode
        ctk.set_appearance_mode("Dark" if mode == "Dark" else "Light")
        ctk.set_default_color_theme("blue")

    def toggle_theme(self, _event=None):
        new = "Dark" if self._theme == "Light" else "Light"
        self._apply_theme(new)
        # Rebuild all screens
        for s in list(self._screens.keys()):
            del self._screens[s]
        self._screens = {}
        self.show_screen("home")

    # ─────────────────────────────────────────
    # Sidebar
    # ─────────────────────────────────────────
    def _build_sidebar(self):
        """Left navigation sidebar."""
        sidebar_color = COLORS["bg_sidebar"] if self._theme == "Light" else COLORS["bg_dark"]
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=sidebar_color, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo_img = load_ctk_image(LOGO_PATH, (70, 70))
        if logo_img:
            ctk.CTkLabel(self.sidebar, image=logo_img, text="").pack(pady=(24, 4))
        else:
            ctk.CTkLabel(
                self.sidebar, text="🎤", font=("Segoe UI", 48),
                text_color=COLORS["text_light"],
            ).pack(pady=(24, 4))

        ctk.CTkLabel(
            self.sidebar, text=APP_TITLE,
            font=FONT["heading3"], text_color=COLORS["text_light"],
        ).pack()
        ctk.CTkLabel(
            self.sidebar, text=f"v{APP_VERSION}",
            font=FONT["tiny"], text_color=COLORS["text_muted"],
        ).pack(pady=(0, 20))

        # Divider
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["text_muted"]).pack(
            fill="x", padx=16, pady=(0, 12)
        )

        # Nav buttons
        self._nav_buttons = {}
        nav_items = [
            ("🏠  Home",         "home",   SHORTCUTS["start_voice"]),
            ("🎤  Voice Form",   "voice",  SHORTCUTS["start_voice"]),
            ("📝  Manual Form",  "manual", SHORTCUTS["manual_form"]),
            ("📊  Dashboard",    "dash",   SHORTCUTS["dashboard"]),
        ]
        for label, key, shortcut in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                font=FONT["body_bold"],
                fg_color="transparent",
                hover_color=COLORS["primary"],
                text_color=COLORS["text_light"],
                anchor="w",
                height=44,
                corner_radius=8,
                command=lambda k=key: self.show_screen(k),
            )
            btn.pack(fill="x", padx=12, pady=3)
            self._nav_buttons[key] = btn

        # Spacer
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(expand=True, fill="both")

        # Bottom controls
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["text_muted"]).pack(
            fill="x", padx=16, pady=(0, 10)
        )

        # Language selector
        ctk.CTkLabel(
            self.sidebar, text="🌐 Language",
            font=FONT["small"], text_color=COLORS["text_muted"],
        ).pack()
        self._lang_var = ctk.StringVar(value=self._language)
        lang_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=list(LANGUAGES.keys()),
            variable=self._lang_var,
            command=self._on_language_change,
            width=160, height=32,
            fg_color=COLORS["primary_dark"],
            button_color=COLORS["primary"],
        )
        lang_menu.pack(pady=(2, 10))

        # Theme toggle
        self._theme_switch = ctk.CTkSwitch(
            self.sidebar,
            text="Dark Mode",
            font=FONT["small"],
            text_color=COLORS["text_light"],
            command=self.toggle_theme,
            progress_color=COLORS["secondary"],
        )
        self._theme_switch.pack(pady=(0, 6))
        if self._theme == "Dark":
            self._theme_switch.select()

        # Exit
        ctk.CTkButton(
            self.sidebar, text="⏻  Exit",
            font=FONT["small"],
            fg_color=COLORS["error"],
            hover_color="#C62828",
            text_color="white",
            height=36, corner_radius=8,
            command=self._on_exit,
        ).pack(fill="x", padx=12, pady=(0, 16))

    def _on_language_change(self, lang: str):
        self._language = lang
        self.speech.set_language(lang)
        logger.info("Language changed to %s", lang)

    # ─────────────────────────────────────────
    # Content area
    # ─────────────────────────────────────────
    def _build_content_area(self):
        self.content = ctk.CTkFrame(self, fg_color=COLORS["bg_main"], corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

    # ─────────────────────────────────────────
    # Screen navigation
    # ─────────────────────────────────────────
    def show_screen(self, key: str):
        """Hide current screen and show the requested one."""
        # Highlight active nav button
        for k, btn in self._nav_buttons.items():
            btn.configure(fg_color=COLORS["primary"] if k == key else "transparent")

        if self._current_screen:
            self._current_screen.pack_forget()

        if key not in self._screens:
            screen_map = {
                "home":   HomeScreen,
                "voice":  VoiceFormScreen,
                "manual": ManualFormScreen,
                "dash":   DashboardScreen,
            }
            cls = screen_map.get(key)
            if cls:
                self._screens[key] = cls(self.content, self)

        screen = self._screens.get(key)
        if screen:
            screen.pack(fill="both", expand=True)
            self._current_screen = screen

    # ─────────────────────────────────────────
    # Shortcuts
    # ─────────────────────────────────────────
    def _bind_shortcuts(self):
        self.bind(SHORTCUTS["toggle_theme"], self.toggle_theme)
        self.bind(SHORTCUTS["quit"],         lambda e: self._on_exit())
        self.bind(SHORTCUTS["dashboard"],    lambda e: self.show_screen("dash"))
        self.bind(SHORTCUTS["manual_form"],  lambda e: self.show_screen("manual"))
        self.bind(SHORTCUTS["start_voice"],  lambda e: self.show_screen("voice"))

    # ─────────────────────────────────────────
    # Exit
    # ─────────────────────────────────────────
    def _on_exit(self):
        if messagebox.askyesno("Exit", "Are you sure you want to exit VoiceForm AI?"):
            self.tts.stop()
            logger.info("Application closed by user.")
            self.destroy()


# ═══════════════════════════════════════════════════════════════
#  1. Home Screen
# ═══════════════════════════════════════════════════════════════
class HomeScreen(ctk.CTkFrame):
    """Landing screen with banner, stats cards, and navigation buttons."""

    def __init__(self, parent, app: Application):
        super().__init__(parent, fg_color=COLORS["bg_main"], corner_radius=0)
        self.app = app
        self._build()

    def _build(self):
        # ── Scrollable container
        scroll = ctk.CTkScrollableFrame(
            self, fg_color=COLORS["bg_main"], corner_radius=0
        )
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Banner
        self._build_banner(scroll)

        # ── Stats
        self._build_stats(scroll)

        # ── Action buttons
        self._build_actions(scroll)

        # ── Feature cards
        self._build_feature_cards(scroll)

    def _build_banner(self, parent):
        banner_frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS["primary"],
            corner_radius=0,
            height=160,
        )
        banner_frame.pack(fill="x")
        banner_frame.pack_propagate(False)

        # Gradient overlay using canvas
        canvas = tk.Canvas(banner_frame, bg=COLORS["primary"], bd=0, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        def _draw_banner(event=None):
            canvas.delete("all")
            w, h = canvas.winfo_width(), canvas.winfo_height()
            if w < 2:
                return
            # Gradient from primary to secondary
            for i in range(w):
                ratio = i / w
                r = int(0x1E + (0x00 - 0x1E) * ratio)
                g = int(0x88 + (0xBC - 0x88) * ratio)
                b = int(0xE5 + (0xD4 - 0xE5) * ratio)
                color = f"#{r:02x}{g:02x}{b:02x}"
                canvas.create_line(i, 0, i, h, fill=color)

            # Banner image
            banner_img = load_ctk_image(BANNER_PATH, (300, 120))
            if banner_img:
                lbl = ctk.CTkLabel(banner_frame, image=banner_img, text="", fg_color="transparent")
                lbl.place(relx=0.78, rely=0.5, anchor="center")

            # Title text
            canvas.create_text(
                50, h // 2 - 20, text=f"🎤 {APP_TITLE}",
                fill="white", font=("Segoe UI", 26, "bold"), anchor="w"
            )
            canvas.create_text(
                50, h // 2 + 10, text="Voice-Powered Registration | AI Assisted | Accessible",
                fill="#B3E5FC", font=("Segoe UI", 12), anchor="w"
            )
            canvas.create_text(
                50, h // 2 + 30, text=f"v{APP_VERSION}",
                fill="#80DEEA", font=("Segoe UI", 10), anchor="w"
            )

        canvas.bind("<Configure>", _draw_banner)
        self.after(100, _draw_banner)

    def _build_stats(self, parent):
        stats = self.app.db.get_stats()
        cards = [
            ("👥 Total Users",         str(stats["total_users"]),       COLORS["primary"]),
            ("📅 Today's Registrations", str(stats["today_registrations"]), COLORS["secondary"]),
            ("✅ Status",               "Online",                         COLORS["success"]),
            ("🌐 Language",             self.app._language,               COLORS["warning"]),
        ]
        row = ctk.CTkFrame(parent, fg_color=COLORS["bg_main"])
        row.pack(fill="x", padx=20, pady=16)
        for i, (title, value, color) in enumerate(cards):
            card = ctk.CTkFrame(row, fg_color=COLORS["bg_card"], corner_radius=14)
            card.grid(row=0, column=i, padx=8, pady=4, sticky="nsew")
            row.columnconfigure(i, weight=1)

            ctk.CTkFrame(card, width=5, fg_color=color, corner_radius=0).pack(
                side="left", fill="y"
            )
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(side="left", padx=12, pady=14, fill="both", expand=True)
            ctk.CTkLabel(inner, text=value, font=FONT["heading2"],
                         text_color=color).pack(anchor="w")
            ctk.CTkLabel(inner, text=title, font=FONT["small"],
                         text_color=COLORS["text_medium"]).pack(anchor="w")

    def _build_actions(self, parent):
        ctk.CTkLabel(
            parent, text="What would you like to do?",
            font=FONT["heading3"], text_color=COLORS["text_dark"],
        ).pack(anchor="w", padx=28, pady=(4, 8))

        btn_row = ctk.CTkFrame(parent, fg_color=COLORS["bg_main"])
        btn_row.pack(fill="x", padx=20, pady=4)

        actions = [
            ("🎤  Start Voice Form", COLORS["primary"],   "voice"),
            ("📝  Manual Form",      COLORS["secondary"],  "manual"),
            ("📊  View Dashboard",   COLORS["bg_sidebar"], "dash"),
        ]
        for i, (label, color, key) in enumerate(actions):
            btn = ctk.CTkButton(
                btn_row, text=label, font=FONT["subhead"],
                fg_color=color, hover_color=COLORS["primary_dark"],
                height=52, corner_radius=12,
                command=lambda k=key: self.app.show_screen(k),
            )
            btn.grid(row=0, column=i, padx=8, pady=4, sticky="ew")
            btn_row.columnconfigure(i, weight=1)

    def _build_feature_cards(self, parent):
        ctk.CTkLabel(
            parent, text="Features",
            font=FONT["heading3"], text_color=COLORS["text_dark"],
        ).pack(anchor="w", padx=28, pady=(16, 8))

        features = [
            ("🎙️ Voice Input",       "Speak naturally — the app listens and understands you."),
            ("✅ Smart Validation",  "All inputs are validated in real-time with helpful hints."),
            ("🌐 Multi-Language",    "Supports English, Hindi, and Telugu voice commands."),
            ("📊 Rich Dashboard",    "View, search, edit, and delete records with ease."),
            ("📄 Export Reports",    "Export data to Excel or PDF with one click."),
            ("🌙 Dark/Light Mode",  "Switch between themes for comfortable viewing."),
        ]

        grid = ctk.CTkFrame(parent, fg_color=COLORS["bg_main"])
        grid.pack(fill="x", padx=20, pady=(0, 24))

        for i, (title, desc) in enumerate(features):
            card = ctk.CTkFrame(grid, fg_color=COLORS["bg_card"], corner_radius=12)
            card.grid(row=i // 3, column=i % 3, padx=8, pady=8, sticky="nsew")
            grid.columnconfigure(i % 3, weight=1)

            ctk.CTkLabel(card, text=title, font=FONT["body_bold"],
                         text_color=COLORS["primary"]).pack(anchor="w", padx=14, pady=(12, 2))
            ctk.CTkLabel(card, text=desc, font=FONT["small"],
                         text_color=COLORS["text_medium"],
                         wraplength=200, justify="left").pack(anchor="w", padx=14, pady=(0, 12))


# ═══════════════════════════════════════════════════════════════
#  2. Voice Form Screen
# ═══════════════════════════════════════════════════════════════
class VoiceFormScreen(ctk.CTkFrame):
    """Guided voice registration form with animated mic and step-by-step fields."""

    def __init__(self, parent, app: Application):
        super().__init__(parent, fg_color=COLORS["bg_main"], corner_radius=0)
        self.app       = app
        self._step     = 0
        self._data     = {}
        self._is_listening  = False
        self._stop_flag     = False
        self._pulse_job     = None
        self._build()

    # ─────────────────────────────────────────
    # Build UI
    # ─────────────────────────────────────────
    def _build(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["primary"], corner_radius=0, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="🎤  Voice Registration Form",
            font=FONT["heading2"], text_color="white",
        ).pack(side="left", padx=24, pady=18)

        # Language indicator
        self._lang_lbl = ctk.CTkLabel(
            header, text=f"🌐 {self.app._language}",
            font=FONT["small"], text_color="#B3E5FC",
        )
        self._lang_lbl.pack(side="right", padx=24)

        # Content area
        content = ctk.CTkFrame(self, fg_color=COLORS["bg_main"])
        content.pack(fill="both", expand=True, padx=24, pady=16)

        # Left panel — mic animation + status
        left = ctk.CTkFrame(content, fg_color=COLORS["bg_card"], corner_radius=16, width=300)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)
        self._build_mic_panel(left)

        # Right panel — form preview
        right = ctk.CTkFrame(content, fg_color=COLORS["bg_card"], corner_radius=16)
        right.pack(side="left", fill="both", expand=True)
        self._build_form_panel(right)

    def _build_mic_panel(self, parent):
        ctk.CTkLabel(
            parent, text="Voice Assistant",
            font=FONT["heading3"], text_color=COLORS["primary"],
        ).pack(pady=(20, 4))
        ctk.CTkLabel(
            parent, text="Speak when the mic is active",
            font=FONT["small"], text_color=COLORS["text_medium"],
        ).pack()

        # Mic canvas (animated)
        self._mic_canvas = tk.Canvas(
            parent, width=160, height=160,
            bg=COLORS["bg_card"], highlightthickness=0,
        )
        self._mic_canvas.pack(pady=20)
        self._draw_mic(listening=False)

        # Status badge
        self._status_var = ctk.StringVar(value="🟡  Ready")
        self._status_lbl = ctk.CTkLabel(
            parent, textvariable=self._status_var,
            font=FONT["body_bold"], text_color=COLORS["warning"],
        )
        self._status_lbl.pack(pady=4)

        # Progress bar
        ctk.CTkLabel(parent, text="Field Progress", font=FONT["small"],
                     text_color=COLORS["text_medium"]).pack(pady=(12, 2))
        self._progress = ctk.CTkProgressBar(parent, width=220, height=12,
                                            progress_color=COLORS["secondary"])
        self._progress.set(0)
        self._progress.pack(pady=4)
        self._progress_lbl = ctk.CTkLabel(
            parent, text="0 / 7 fields", font=FONT["small"],
            text_color=COLORS["text_medium"],
        )
        self._progress_lbl.pack()

        # Question display
        ctk.CTkLabel(parent, text="Current Question:", font=FONT["small"],
                     text_color=COLORS["text_muted"]).pack(pady=(16, 2))
        self._question_var = ctk.StringVar(value="Press 'Start' to begin")
        self._question_lbl = ctk.CTkLabel(
            parent, textvariable=self._question_var,
            font=FONT["body"], text_color=COLORS["text_dark"],
            wraplength=240, justify="center",
        )
        self._question_lbl.pack(padx=12)

        # Recognised text
        ctk.CTkLabel(parent, text="I heard:", font=FONT["small"],
                     text_color=COLORS["text_muted"]).pack(pady=(12, 2))
        self._heard_var = ctk.StringVar(value="—")
        ctk.CTkLabel(
            parent, textvariable=self._heard_var,
            font=FONT["body_bold"], text_color=COLORS["secondary"],
            wraplength=240, justify="center",
        ).pack(padx=12)

        # Buttons
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(pady=20, fill="x", padx=16)

        self._start_btn = ctk.CTkButton(
            btn_frame, text="▶  Start Voice Form",
            font=FONT["body_bold"], height=44, corner_radius=10,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"],
            command=self._start_voice_form,
        )
        self._start_btn.pack(fill="x", pady=4)

        self._stop_btn = ctk.CTkButton(
            btn_frame, text="⏹  Stop",
            font=FONT["body"], height=36, corner_radius=10,
            fg_color=COLORS["error"], hover_color="#C62828",
            command=self._stop_voice_form, state="disabled",
        )
        self._stop_btn.pack(fill="x", pady=4)

        self._reset_btn = ctk.CTkButton(
            btn_frame, text="🔄  Reset",
            font=FONT["body"], height=36, corner_radius=10,
            fg_color="transparent", border_width=2,
            border_color=COLORS["primary"],
            text_color=COLORS["primary"],
            hover_color=COLORS["bg_main"],
            command=self._reset_form,
        )
        self._reset_btn.pack(fill="x", pady=4)

    def _build_form_panel(self, parent):
        ctk.CTkLabel(
            parent, text="📋  Form Preview",
            font=FONT["heading3"], text_color=COLORS["primary"],
        ).pack(anchor="w", padx=20, pady=(20, 4))
        ctk.CTkLabel(
            parent, text="Fields are filled automatically as you speak.",
            font=FONT["small"], text_color=COLORS["text_medium"],
        ).pack(anchor="w", padx=20, pady=(0, 12))

        ctk.CTkFrame(parent, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=20)

        # Field entries
        scroll_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=16, pady=8)

        self._field_vars   = {}
        self._field_labels = {}

        for field in FORM_FIELDS:
            key   = field["key"]
            label = field["label"]
            icon  = field["icon"]

            row = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_main"], corner_radius=10)
            row.pack(fill="x", pady=4)

            # Icon + label
            lbl_frame = ctk.CTkFrame(row, fg_color="transparent", width=130)
            lbl_frame.pack(side="left", padx=(12, 4), pady=10)
            lbl_frame.pack_propagate(False)
            ctk.CTkLabel(lbl_frame, text=f"{icon} {label}",
                         font=FONT["body_bold"], text_color=COLORS["text_dark"],
                         anchor="w").pack(fill="x")

            # Status dot
            dot = ctk.CTkLabel(row, text="⬜", font=("Segoe UI", 14))
            dot.pack(side="left", padx=4)
            self._field_labels[key] = dot

            # Value entry (read-only during voice, editable after)
            var = ctk.StringVar(value="")
            entry = ctk.CTkEntry(
                row, textvariable=var, font=FONT["body"],
                width=320, height=36, corner_radius=8,
                border_color=COLORS["border"],
                fg_color=COLORS["bg_card"],
                state="disabled",
            )
            entry.pack(side="left", padx=8, pady=10, fill="x", expand=True)
            self._field_vars[key] = (var, entry)

        # Submit button
        ctk.CTkFrame(parent, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=20)
        self._submit_voice_btn = ctk.CTkButton(
            parent, text="✔  Submit Registration",
            font=FONT["subhead"], height=48, corner_radius=12,
            fg_color=COLORS["success"], hover_color="#2E7D32",
            command=self._submit_form, state="disabled",
        )
        self._submit_voice_btn.pack(fill="x", padx=20, pady=16)

    # ─────────────────────────────────────────
    # Mic animation
    # ─────────────────────────────────────────
    def _draw_mic(self, listening: bool = False, pulse_r: int = 0):
        c = self._mic_canvas
        c.delete("all")
        cx, cy = 80, 80

        # Pulse rings (when listening)
        if listening:
            for r in [55 + pulse_r, 65 + pulse_r]:
                alpha = max(0, 180 - pulse_r * 3)
                color = COLORS["secondary"] if r < 70 + pulse_r else COLORS["primary_light"]
                c.create_oval(cx - r, cy - r, cx + r, cy + r,
                              outline=color, width=2)

        # Mic body
        body_color = COLORS["secondary"] if listening else COLORS["primary"]
        c.create_rectangle(cx - 20, cy - 40, cx + 20, cy + 10,
                           fill=body_color, outline="", width=0)
        c.create_oval(cx - 20, cy - 50, cx + 20, cy - 30,
                      fill=body_color, outline="")
        c.create_oval(cx - 20, cy, cx + 20, cy + 20,
                      fill=body_color, outline="")

        # Stand
        c.create_arc(cx - 35, cy - 10, cx + 35, cy + 50,
                     start=0, extent=180, style=tk.ARC,
                     outline=body_color, width=3)
        c.create_line(cx, cy + 46, cx, cy + 65, fill=body_color, width=3)
        c.create_line(cx - 20, cy + 65, cx + 20, cy + 65, fill=body_color, width=3)

        # Listening indicator text
        if listening:
            c.create_text(cx, cy + 82, text="● Listening…",
                          fill=COLORS["secondary"], font=("Segoe UI", 9, "bold"))
        else:
            c.create_text(cx, cy + 82, text="○ Idle",
                          fill=COLORS["text_muted"], font=("Segoe UI", 9))

    def _start_pulse(self):
        """Animate the microphone pulse ring."""
        self._pulse_r = 0

        def _pulse():
            if not self._is_listening:
                self._draw_mic(listening=False)
                return
            self._pulse_r = (self._pulse_r + 3) % 18
            self._draw_mic(listening=True, pulse_r=self._pulse_r)
            self._pulse_job = self.after(80, _pulse)

        _pulse()

    def _stop_pulse(self):
        if self._pulse_job:
            self.after_cancel(self._pulse_job)
            self._pulse_job = None
        self._draw_mic(listening=False)

    # ─────────────────────────────────────────
    # Voice form logic
    # ─────────────────────────────────────────
    def _start_voice_form(self):
        if not self.app.speech.is_available:
            from speech import _PYAUDIO_AVAILABLE, _SR_AVAILABLE
            if not _PYAUDIO_AVAILABLE:
                messagebox.showwarning(
                    "PyAudio Not Installed",
                    "PyAudio is required for microphone access but could not be found.\n\n"
                    "On Python 3.14, no pre-built wheel exists yet.\n"
                    "You can either:\n"
                    "  1. Install Microsoft C++ Build Tools, then:\n"
                    "       pip install pyaudio\n\n"
                    "  2. Or use the Manual Form (📝) instead — it has a\n"
                    "     'Voice Fill' button that also works once PyAudio is installed.\n\n"
                    "The rest of the app (manual form, dashboard, export) works fully!",
                )
            else:
                messagebox.showerror(
                    "Microphone Error",
                    "No microphone detected.\nPlease connect a microphone and restart.",
                )
            return
        self._stop_flag = False
        self._step      = 0
        self._data      = {}
        self._reset_field_ui()
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        threading.Thread(target=self._run_voice_form, daemon=True).start()

    def _stop_voice_form(self):
        self._stop_flag = True
        self._is_listening = False
        self._stop_pulse()
        self._set_status("⛔  Stopped", COLORS["error"])
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")

    def _reset_form(self):
        self._stop_voice_form()
        self._data = {}
        self._step = 0
        self._reset_field_ui()
        self._question_var.set("Press 'Start' to begin")
        self._heard_var.set("—")
        self._submit_voice_btn.configure(state="disabled")
        self._update_progress(0)

    def _reset_field_ui(self):
        for key, (var, entry) in self._field_vars.items():
            var.set("")
            self._field_labels[key].configure(text="⬜")

    def _set_status(self, text: str, color: str):
        self._status_var.set(text)
        self._status_lbl.configure(text_color=color)

    def _update_progress(self, step: int):
        total = len(FORM_FIELDS)
        val   = step / total
        self._progress.set(val)
        self._progress_lbl.configure(text=f"{step} / {total} fields")

    # ─────────────────────────────────────────
    # Core voice loop (runs in background thread)
    # ─────────────────────────────────────────
    def _run_voice_form(self):
        """Step through each form field using TTS + speech recognition."""
        # Calibrate mic
        self._set_status("🔧  Calibrating…", COLORS["warning"])
        self.app.speech.calibrate()

        for i, field in enumerate(FORM_FIELDS):
            if self._stop_flag:
                break

            key   = field["key"]
            label = field["label"]

            confirmed = False
            while not confirmed and not self._stop_flag:
                # Ask question via TTS
                self._question_var.set(field["question"])
                self.app.tts.speak(field["question"], block=True)

                if self._stop_flag:
                    break

                # Start listening
                self._is_listening = True
                self._set_status("🎙️  Listening…", COLORS["secondary"])
                self.after(0, self._start_pulse)

                try:
                    raw_text = self.app.speech.listen(timeout=10)
                except MicrophoneNotFoundError:
                    self._set_status("❌  No Mic", COLORS["error"])
                    messagebox.showerror("Error", "Microphone not found.")
                    self._stop_voice_form()
                    return
                except SpeechRecognitionError as exc:
                    self._set_status("⚠️  Not Heard", COLORS["warning"])
                    self.app.tts.speak("I couldn't hear you. Please try again.", block=True)
                    self._heard_var.set("(not recognised)")
                    self._is_listening = False
                    self.after(0, self._stop_pulse)
                    continue

                # Stop animation
                self._is_listening = False
                self.after(0, self._stop_pulse)
                self._set_status("⚙️  Processing…", COLORS["info"])

                # Normalise based on field type
                normalised = self._normalise(key, raw_text)

                # Validate
                ok, err_msg = self._validate_field(key, normalised)
                if not ok:
                    self._heard_var.set(f"⚠ {normalised}")
                    self.app.tts.announce_validation_error(label, err_msg)
                    continue

                # Display recognised text
                self._heard_var.set(normalised)
                self._set_status("🤔  Confirming…", COLORS["primary"])

                # Confirm via TTS + voice
                confirm_text = field["confirm"].format(normalised)
                self.app.tts.speak(confirm_text, block=True)

                if self._stop_flag:
                    break

                # Listen for Yes/No
                self._is_listening = True
                self._set_status("🎙️  Say Yes/No", COLORS["secondary"])
                self.after(0, self._start_pulse)
                answer = self.app.speech.listen_for_confirmation()
                self._is_listening = False
                self.after(0, self._stop_pulse)

                if answer is True:
                    confirmed = True
                    self._data[key] = normalised
                    # Update UI field
                    var, entry = self._field_vars[key]
                    var.set(normalised)
                    self._field_labels[key].configure(text="✅")
                    self._update_progress(i + 1)
                    self._set_status(f"✅  {label} saved", COLORS["success"])
                elif answer is False:
                    self.app.tts.speak("Let me ask that again.", block=True)
                else:
                    self.app.tts.speak("I didn't catch that. Let me repeat.", block=True)

        # All fields done
        if not self._stop_flag and len(self._data) == len(FORM_FIELDS):
            self._set_status("✅  All fields complete!", COLORS["success"])
            self.app.tts.speak(
                "All fields have been filled. Please click Submit to save your registration.",
                block=True,
            )
            self.after(0, lambda: self._submit_voice_btn.configure(state="normal"))
        elif not self._stop_flag:
            self._set_status("⚠️  Incomplete", COLORS["warning"])

        self.after(0, lambda: self._start_btn.configure(state="normal"))
        self.after(0, lambda: self._stop_btn.configure(state="disabled"))

    def _normalise(self, key: str, text: str) -> str:
        """Apply field-specific normalization to speech text."""
        v = self.app.validator
        if key == "gender":   return v.normalise_gender(text)
        if key == "age":      return v.normalise_age(text)
        if key == "phone":    return v.normalise_phone(text)
        if key == "email":    return v.normalise_email(text)
        if key == "name":     return text.strip().title()
        return text.strip()

    def _validate_field(self, key: str, value: str) -> tuple[bool, str]:
        """Dispatch to the correct Validator method."""
        v = self.app.validator
        dispatch = {
            "name":       v.validate_name,
            "age":        v.validate_age,
            "gender":     v.validate_gender,
            "phone":      v.validate_phone,
            "email":      v.validate_email,
            "address":    v.validate_address,
            "occupation": v.validate_occupation,
        }
        fn = dispatch.get(key)
        return fn(value) if fn else (True, "")

    def _submit_form(self):
        """Insert validated data into the database."""
        errors = self.app.validator.validate_all(self._data)
        if errors:
            msg = "\n".join(f"{k}: {v}" for k, v in errors.items())
            messagebox.showerror("Validation Error", f"Please fix:\n{msg}")
            return
        try:
            row_id = self.app.db.insert_user(self._data)
            self.app.tts.announce_success()
            self._show_success_dialog(row_id)
            self._reset_form()
            # Refresh dashboard if open
            if "dash" in self.app._screens:
                self.app._screens["dash"].refresh()
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))

    def _show_success_dialog(self, row_id: int):
        win = ctk.CTkToplevel(self)
        win.title("Registration Successful")
        win.geometry("400x360")
        win.grab_set()
        win.resizable(False, False)

        img = load_ctk_image(SUCCESS_PATH, (90, 90))
        if img:
            ctk.CTkLabel(win, image=img, text="").pack(pady=20)
        else:
            ctk.CTkLabel(win, text="✅", font=("Segoe UI", 56)).pack(pady=20)

        ctk.CTkLabel(win, text="Registration Successful!",
                     font=FONT["heading2"], text_color=COLORS["success"]).pack()
        ctk.CTkLabel(win, text=f"User ID: #{row_id}  |  {self._data.get('name', '')}",
                     font=FONT["body"], text_color=COLORS["text_medium"]).pack(pady=4)
        ctk.CTkButton(win, text="Go to Dashboard", height=40, corner_radius=10,
                      command=lambda: [win.destroy(), self.app.show_screen("dash")]
                      ).pack(pady=12, padx=40, fill="x")
        ctk.CTkButton(win, text="Close", height=36, corner_radius=10,
                      fg_color="transparent", border_width=2,
                      border_color=COLORS["border"],
                      text_color=COLORS["text_medium"],
                      command=win.destroy).pack(padx=40, fill="x")


# ═══════════════════════════════════════════════════════════════
#  3. Manual Form Screen
# ═══════════════════════════════════════════════════════════════
class ManualFormScreen(ctk.CTkFrame):
    """Keyboard-based registration form with validation and optional voice-fill."""

    def __init__(self, parent, app: Application):
        super().__init__(parent, fg_color=COLORS["bg_main"], corner_radius=0)
        self.app      = app
        self._edit_id = None   # If set, we are editing an existing record
        self._build()

    def _build(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["primary"], corner_radius=0, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="📝  Manual Registration Form",
            font=FONT["heading2"], text_color="white",
        ).pack(side="left", padx=24, pady=18)

        # Form card
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=16)
        card.pack(fill="both", expand=True, padx=24, pady=20)

        scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        self._entries = {}
        self._error_labels = {}

        for field in FORM_FIELDS:
            self._add_field(scroll, field)

        # Button row
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=16)

        buttons = [
            ("✔  Submit",      COLORS["success"],  self._submit),
            ("🎤  Voice Fill", COLORS["primary"],   self._voice_fill_all),
            ("🔄  Reset",      COLORS["warning"],   self._reset),
            ("🗑  Clear",      COLORS["error"],     self._clear),
        ]
        for i, (label, color, cmd) in enumerate(buttons):
            btn = ctk.CTkButton(
                btn_row, text=label, font=FONT["body_bold"],
                fg_color=color, hover_color=COLORS["primary_dark"],
                height=46, corner_radius=10,
                command=cmd,
            )
            btn.grid(row=0, column=i, padx=6, pady=4, sticky="ew")
            btn_row.columnconfigure(i, weight=1)

    def _add_field(self, parent, field: dict):
        key   = field["key"]
        label = field["label"]
        icon  = field["icon"]

        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_main"], corner_radius=10)
        frame.pack(fill="x", padx=16, pady=6)

        # Label
        ctk.CTkLabel(
            frame, text=f"{icon}  {label}",
            font=FONT["body_bold"], text_color=COLORS["text_dark"],
            width=150, anchor="w",
        ).pack(side="left", padx=(16, 4), pady=12)

        right = ctk.CTkFrame(frame, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True, padx=(0, 16))

        # Special widgets for gender
        if key == "gender":
            var = ctk.StringVar(value="Male")
            widget = ctk.CTkOptionMenu(
                right, values=["Male", "Female", "Other"],
                variable=var, width=300, height=38, corner_radius=8,
            )
            widget.pack(anchor="w", pady=8)
        else:
            var = ctk.StringVar()
            widget = ctk.CTkEntry(
                right, textvariable=var, font=FONT["body"],
                width=360, height=40, corner_radius=8,
                border_color=COLORS["border"],
                placeholder_text=f"Enter your {label.lower()}…",
            )
            widget.pack(anchor="w", pady=8)

        # Error label
        err_lbl = ctk.CTkLabel(right, text="", font=FONT["small"],
                               text_color=COLORS["error"], anchor="w")
        err_lbl.pack(anchor="w")

        self._entries[key]      = var
        self._error_labels[key] = err_lbl

    def _submit(self):
        data   = {k: v.get().strip() for k, v in self._entries.items()}
        errors = self.app.validator.validate_all(data)

        # Clear previous errors
        for key, lbl in self._error_labels.items():
            lbl.configure(text="")

        if errors:
            for key, msg in errors.items():
                self._error_labels[key].configure(text=f"⚠ {msg}")
            self.app.tts.speak("Please fix the highlighted errors before submitting.", block=False)
            return

        try:
            if self._edit_id:
                self.app.db.update_user(self._edit_id, data)
                messagebox.showinfo("Updated", f"Record #{self._edit_id} updated successfully!")
                self._edit_id = None
            else:
                row_id = self.app.db.insert_user(data)
                self.app.tts.announce_success()
                messagebox.showinfo("Success", f"Registration successful! ID: #{row_id}")
            self._clear()
            if "dash" in self.app._screens:
                self.app._screens["dash"].refresh()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _reset(self):
        self._clear()
        self._edit_id = None

    def _clear(self):
        for key, var in self._entries.items():
            var.set("Male" if key == "gender" else "")
        for lbl in self._error_labels.values():
            lbl.configure(text="")

    def _voice_fill_all(self):
        """Use voice to fill each field in sequence."""
        if not self.app.speech.is_available:
            messagebox.showerror("Mic Error", "No microphone detected.")
            return
        threading.Thread(target=self._do_voice_fill, daemon=True).start()

    def _do_voice_fill(self):
        """Run voice fill for all fields in the manual form."""
        self.app.tts.speak("I will now fill the form using your voice.", block=True)
        v = self.app.validator

        for field in FORM_FIELDS:
            key   = field["key"]
            label = field["label"]
            self.app.tts.speak(field["question"], block=True)

            for attempt in range(3):
                try:
                    raw = self.app.speech.listen(timeout=10)
                except SpeechRecognitionError:
                    self.app.tts.speak("Could not hear you. Trying again.", block=True)
                    continue

                # Normalise
                normalised = self._normalise(key, raw)

                # Validate
                fn_map = {
                    "name": v.validate_name, "age": v.validate_age,
                    "gender": v.validate_gender, "phone": v.validate_phone,
                    "email": v.validate_email, "address": v.validate_address,
                    "occupation": v.validate_occupation,
                }
                fn = fn_map.get(key)
                ok, err = fn(normalised) if fn else (True, "")
                if not ok:
                    self.app.tts.speak(f"Invalid {label}: {err}. Try again.", block=True)
                    continue

                # Confirm
                self.app.tts.speak(field["confirm"].format(normalised), block=True)
                answer = self.app.speech.listen_for_confirmation()
                if answer is True:
                    self._entries[key].set(normalised)
                    break
                elif answer is False:
                    self.app.tts.speak("Let me ask again.", block=True)
                else:
                    self.app.tts.speak("Setting the value and moving on.", block=True)
                    self._entries[key].set(normalised)
                    break

    def _normalise(self, key: str, text: str) -> str:
        v = self.app.validator
        if key == "gender":   return v.normalise_gender(text)
        if key == "age":      return v.normalise_age(text)
        if key == "phone":    return v.normalise_phone(text)
        if key == "email":    return v.normalise_email(text)
        if key == "name":     return text.strip().title()
        return text.strip()

    def load_record(self, record: dict):
        """Pre-fill the form with an existing record for editing."""
        self._edit_id = record.get("id")
        for key, var in self._entries.items():
            var.set(str(record.get(key, "")))


# ═══════════════════════════════════════════════════════════════
#  4. Dashboard Screen
# ═══════════════════════════════════════════════════════════════
class DashboardScreen(ctk.CTkFrame):
    """Records table with search, edit, delete, and export actions."""

    def __init__(self, parent, app: Application):
        super().__init__(parent, fg_color=COLORS["bg_main"], corner_radius=0)
        self.app          = app
        self._all_records = []
        self._build()
        self.refresh()

    # ─────────────────────────────────────────
    def _build(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["primary"], corner_radius=0, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="📊  Dashboard",
            font=FONT["heading2"], text_color="white",
        ).pack(side="left", padx=24, pady=18)
        ctk.CTkLabel(
            header, text="Manage all registrations",
            font=FONT["small"], text_color="#B3E5FC",
        ).pack(side="left")

        # Stats row
        self._stats_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_main"])
        self._stats_frame.pack(fill="x", padx=20, pady=(12, 4))

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        toolbar.pack(fill="x", padx=20, pady=4)

        # Search
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_search)
        ctk.CTkLabel(toolbar, text="🔍", font=("Segoe UI", 18)).pack(side="left", padx=(12, 4), pady=10)
        ctk.CTkEntry(
            toolbar, textvariable=self._search_var, width=280, height=36,
            font=FONT["body"], placeholder_text="Search by name, email, phone…",
            corner_radius=8, border_color=COLORS["border"],
        ).pack(side="left", padx=4, pady=10)

        # Voice search
        ctk.CTkButton(
            toolbar, text="🎤", width=40, height=36, corner_radius=8,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"],
            command=self._voice_search,
        ).pack(side="left", padx=4)

        # Right-side action buttons
        for label, color, cmd in [
            ("➕ Add",         COLORS["success"],    lambda: self.app.show_screen("manual")),
            ("✏️ Edit",        COLORS["primary"],    self._edit_selected),
            ("🗑 Delete",      COLORS["error"],      self._delete_selected),
            ("📊 Excel",       COLORS["secondary"],  self._export_excel),
            ("📄 PDF",         COLORS["bg_sidebar"], self._export_pdf),
            ("💾 Backup",      COLORS["warning"],    self._backup),
            ("🔄 Refresh",     COLORS["text_medium"],self.refresh),
        ]:
            ctk.CTkButton(
                toolbar, text=label, font=FONT["small"],
                fg_color=color, hover_color=COLORS["primary_dark"],
                height=36, corner_radius=8, width=80,
                command=cmd,
            ).pack(side="right", padx=4, pady=10)

        # Table
        table_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=20, pady=8)
        self._build_table(table_frame)

        # Status bar
        self._status_bar = ctk.CTkLabel(
            self, text="", font=FONT["small"], text_color=COLORS["text_medium"],
        )
        self._status_bar.pack(anchor="w", padx=24, pady=(0, 8))

    def _build_table(self, parent):
        """Build the ttk.Treeview table with scrollbars."""
        # Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
            background=COLORS["bg_card"],
            foreground=COLORS["text_dark"],
            rowheight=34,
            fieldbackground=COLORS["bg_card"],
            font=("Segoe UI", 10),
        )
        style.configure("Custom.Treeview.Heading",
            background=COLORS["primary"],
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map("Custom.Treeview",
            background=[("selected", COLORS["primary_light"])],
            foreground=[("selected", COLORS["text_dark"])],
        )
        style.map("Custom.Treeview.Heading",
            background=[("active", COLORS["primary_dark"])],
        )

        columns = ("id", "name", "age", "gender", "phone", "email",
                   "address", "occupation", "reg_date", "reg_time")
        col_widths = {
            "id": 40, "name": 130, "age": 50, "gender": 70,
            "phone": 100, "email": 160, "address": 180,
            "occupation": 100, "reg_date": 90, "reg_time": 80,
        }
        col_labels = {
            "id": "#", "name": "Name", "age": "Age", "gender": "Gender",
            "phone": "Phone", "email": "Email", "address": "Address",
            "occupation": "Occupation", "reg_date": "Date", "reg_time": "Time",
        }

        # Scrollbars
        vsb = ttk.Scrollbar(parent, orient="vertical")
        hsb = ttk.Scrollbar(parent, orient="horizontal")

        self._tree = ttk.Treeview(
            parent, columns=columns, show="headings",
            style="Custom.Treeview",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
        )
        vsb.configure(command=self._tree.yview)
        hsb.configure(command=self._tree.xview)

        for col in columns:
            self._tree.heading(col, text=col_labels[col],
                               command=lambda c=col: self._sort_by(c))
            self._tree.column(col, width=col_widths.get(col, 100),
                              anchor="center" if col in ("id", "age", "gender") else "w")

        # Alternate row colours
        self._tree.tag_configure("even", background="#EAF3FB")
        self._tree.tag_configure("odd",  background=COLORS["bg_card"])

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Double-click to edit
        self._tree.bind("<Double-1>", lambda e: self._edit_selected())

    # ─────────────────────────────────────────
    # Data loading
    # ─────────────────────────────────────────
    def refresh(self):
        """Reload all records from the database."""
        self._all_records = self.app.db.get_all_users()
        self._populate_table(self._all_records)
        self._update_stats()
        self._status_bar.configure(text=f"✅ Loaded {len(self._all_records)} records.")

    def _populate_table(self, records: list[dict]):
        """Clear and repopulate the treeview."""
        self._tree.delete(*self._tree.get_children())
        for i, rec in enumerate(records):
            tag = "even" if i % 2 == 0 else "odd"
            self._tree.insert("", "end", iid=str(rec["id"]), tag=tag, values=(
                rec.get("id"), rec.get("name"), rec.get("age"), rec.get("gender"),
                rec.get("phone"), rec.get("email"), rec.get("address"),
                rec.get("occupation"), rec.get("reg_date"), rec.get("reg_time"),
            ))

    def _update_stats(self):
        # Clear old cards
        for w in self._stats_frame.winfo_children():
            w.destroy()

        stats = self.app.db.get_stats()
        cards_data = [
            ("👥 Total",      str(stats["total_users"]),          COLORS["primary"]),
            ("📅 Today",      str(stats["today_registrations"]),  COLORS["secondary"]),
            ("🕒 Latest",
             stats["latest_user"]["name"] if stats["latest_user"] else "—",
             COLORS["success"]),
        ]
        for i, (title, value, color) in enumerate(cards_data):
            card = ctk.CTkFrame(self._stats_frame, fg_color=COLORS["bg_card"],
                                corner_radius=12)
            card.grid(row=0, column=i, padx=6, sticky="ew")
            self._stats_frame.columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=value, font=FONT["heading2"],
                         text_color=color).pack(padx=14, pady=(8, 0))
            ctk.CTkLabel(card, text=title, font=FONT["small"],
                         text_color=COLORS["text_medium"]).pack(padx=14, pady=(0, 8))

    # ─────────────────────────────────────────
    # Search
    # ─────────────────────────────────────────
    def _on_search(self, *_):
        q = self._search_var.get().strip()
        if not q:
            self._populate_table(self._all_records)
            return
        results = self.app.db.search_users(q)
        self._populate_table(results)
        self._status_bar.configure(text=f"🔍 Found {len(results)} matching record(s).")

    def _voice_search(self):
        def _search():
            self.app.tts.speak("Please say the name or phone number to search.", block=True)
            try:
                query = self.app.speech.listen(timeout=8)
                self._search_var.set(query)
            except SpeechRecognitionError:
                self.app.tts.speak("Could not recognise. Please type instead.", block=False)

        threading.Thread(target=_search, daemon=True).start()

    # ─────────────────────────────────────────
    # Sort
    # ─────────────────────────────────────────
    def _sort_by(self, col: str):
        records = self.app.db.get_all_users()
        try:
            records.sort(key=lambda r: (r.get(col) or ""), reverse=False)
        except TypeError:
            pass
        self._populate_table(records)

    # ─────────────────────────────────────────
    # Edit
    # ─────────────────────────────────────────
    def _edit_selected(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Select a Record", "Please select a record to edit.")
            return
        rec_id = int(sel[0])
        record = self.app.db.get_user_by_id(rec_id)
        if not record:
            messagebox.showerror("Error", "Record not found.")
            return
        # Switch to manual form and pre-fill
        self.app.show_screen("manual")
        manual: ManualFormScreen = self.app._screens.get("manual")
        if manual:
            manual.load_record(record)

    # ─────────────────────────────────────────
    # Delete
    # ─────────────────────────────────────────
    def _delete_selected(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Select a Record", "Please select a record to delete.")
            return
        rec_id = int(sel[0])
        name   = self._tree.set(sel[0], "name")
        if not messagebox.askyesno("Confirm Delete",
                f"Delete record #{rec_id} — {name}?\nThis cannot be undone."):
            return
        if self.app.db.delete_user(rec_id):
            self._status_bar.configure(text=f"🗑 Deleted record #{rec_id}.")
            self.refresh()
        else:
            messagebox.showerror("Error", "Failed to delete record.")

    # ─────────────────────────────────────────
    # Export
    # ─────────────────────────────────────────
    def _export_excel(self):
        records = self.app.db.get_all_users()
        if not records:
            messagebox.showinfo("No Data", "No records to export.")
            return
        try:
            path = self.app.exporter.export_to_excel(records)
            if messagebox.askyesno("Exported", f"Excel saved to:\n{path}\n\nOpen the file?"):
                os.startfile(path)
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))

    def _export_pdf(self):
        records = self.app.db.get_all_users()
        if not records:
            messagebox.showinfo("No Data", "No records to export.")
            return
        try:
            path = self.app.exporter.export_to_pdf(records)
            if messagebox.askyesno("Exported", f"PDF saved to:\n{path}\n\nOpen the file?"):
                os.startfile(path)
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))

    def _backup(self):
        try:
            path = self.app.db.backup_database()
            messagebox.showinfo("Backup Successful", f"Database backed up to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Backup Error", str(exc))
