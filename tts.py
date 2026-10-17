"""
tts.py — Text-to-Speech engine wrapper using pyttsx3.
Provides non-blocking speech synthesis with language and voice controls.
"""

import pyttsx3
import threading
import logging
from config import TTS_RATE_DEFAULT, TTS_VOLUME

logger = logging.getLogger(__name__)


class TTSEngine:
    """
    Thread-safe Text-to-Speech engine using pyttsx3.

    Usage
    -----
    tts = TTSEngine()
    tts.speak("Welcome to VoiceForm AI!")
    """

    def __init__(self):
        self._engine  = None
        self._lock    = threading.Lock()
        self._speaking = False
        self._init_engine()
        logger.info("TTSEngine initialised.")

    # ─────────────────────────────────────────
    # Initialise
    # ─────────────────────────────────────────
    def _init_engine(self):
        """Create and configure the pyttsx3 engine."""
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate",   TTS_RATE_DEFAULT)
            self._engine.setProperty("volume", TTS_VOLUME)
            self._set_default_voice()
        except Exception as exc:
            logger.error("TTSEngine init failed: %s", exc)
            self._engine = None

    def _set_default_voice(self):
        """Select the first available English voice."""
        if not self._engine:
            return
        voices = self._engine.getProperty("voices")
        for v in voices:
            if "english" in v.name.lower() or "zira" in v.name.lower():
                self._engine.setProperty("voice", v.id)
                logger.debug("TTS voice set to: %s", v.name)
                return
        if voices:
            self._engine.setProperty("voice", voices[0].id)

    # ─────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────
    def speak(self, text: str, block: bool = False):
        """
        Speak the given text.

        Parameters
        ----------
        text  : str   The text to speak.
        block : bool  If True, wait for speech to finish before returning.
        """
        if not self._engine:
            logger.warning("TTS engine not available. Text: %s", text)
            return
        if block:
            self._speak_now(text)
        else:
            t = threading.Thread(target=self._speak_now, args=(text,), daemon=True)
            t.start()

    def _speak_now(self, text: str):
        """Internal blocking speech call (run in thread)."""
        with self._lock:
            self._speaking = True
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as exc:
                logger.error("TTS speak error: %s", exc)
                # Reinitialise engine on failure
                self._init_engine()
            finally:
                self._speaking = False

    def stop(self):
        """Stop ongoing speech."""
        if self._engine:
            try:
                self._engine.stop()
                self._speaking = False
            except Exception as exc:
                logger.warning("TTS stop error: %s", exc)

    @property
    def is_speaking(self) -> bool:
        """Return True if TTS is currently active."""
        return self._speaking

    # ─────────────────────────────────────────
    # Configuration setters
    # ─────────────────────────────────────────
    def set_rate(self, rate: int):
        """Set speech rate (words per minute). Default: 165."""
        if self._engine:
            self._engine.setProperty("rate", rate)
            logger.debug("TTS rate set to %d", rate)

    def set_volume(self, volume: float):
        """Set volume (0.0 – 1.0). Default: 1.0."""
        if self._engine:
            volume = max(0.0, min(1.0, volume))
            self._engine.setProperty("volume", volume)

    def set_voice_gender(self, gender: str = "female"):
        """
        Switch between available male/female voices.

        Parameters
        ----------
        gender : str  'male' or 'female'
        """
        if not self._engine:
            return
        voices = self._engine.getProperty("voices")
        for v in voices:
            name_lower = v.name.lower()
            if gender == "female" and ("zira" in name_lower or "female" in name_lower or "woman" in name_lower):
                self._engine.setProperty("voice", v.id)
                logger.debug("TTS voice changed to FEMALE: %s", v.name)
                return
            if gender == "male" and ("david" in name_lower or "male" in name_lower or "man" in name_lower):
                self._engine.setProperty("voice", v.id)
                logger.debug("TTS voice changed to MALE: %s", v.name)
                return

    def list_voices(self) -> list[dict]:
        """Return all available voices as a list of dicts."""
        if not self._engine:
            return []
        voices = self._engine.getProperty("voices")
        return [{"id": v.id, "name": v.name, "lang": v.languages} for v in voices]

    # ─────────────────────────────────────────
    # Pre-built announcements
    # ─────────────────────────────────────────
    def welcome(self):
        self.speak(
            "Welcome to VoiceForm AI. "
            "I will guide you through the registration form using voice commands.",
            block=True,
        )

    def announce_field(self, question: str):
        self.speak(question, block=True)

    def confirm_field(self, value: str, field_label: str):
        self.speak(f"I heard {field_label}: {value}. Please say Yes to confirm, or No to retry.")

    def announce_success(self):
        self.speak(
            "Registration successful! Your information has been saved. Thank you.",
            block=True,
        )

    def announce_error(self, message: str):
        self.speak(f"There was an issue: {message}. Please try again.", block=True)

    def announce_validation_error(self, field: str, message: str):
        self.speak(f"Invalid {field}. {message}. Please try again.", block=True)
