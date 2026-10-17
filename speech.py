"""
speech.py — Speech recognition engine for the Voice Form Filling System.

Backend
-------
• sounddevice  — mic capture (no PyAudio / PortAudio required)
• SpeechRecognition + recognize_google()  — free Google STT, no API key needed

Install
-------
    pip install sounddevice scipy numpy SpeechRecognition
"""

import io
import wave
import threading
import logging

# ── Graceful optional imports ──────────────────────────────────────────────────
try:
    import numpy as np
    import sounddevice as sd
    _SD_AVAILABLE = True
except ImportError:
    np = None
    sd = None
    _SD_AVAILABLE = False

try:
    import speech_recognition as sr
    _SR_AVAILABLE = True
except ImportError:
    sr = None
    _SR_AVAILABLE = False

from config import (
    SR_TIMEOUT, SR_PHRASE_LIMIT, SR_MAX_RETRIES,
    SR_RECORD_SECONDS, SR_SAMPLE_RATE, LANGUAGES,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Custom Exceptions
# ─────────────────────────────────────────────
class MicrophoneNotFoundError(Exception):
    """Raised when no microphone input device is detected."""

class SpeechRecognitionError(Exception):
    """Raised when speech cannot be recognised after all retries."""


# ─────────────────────────────────────────────
# Helper: PCM float32 → WAV bytes → AudioData
# ─────────────────────────────────────────────
def _pcm_to_audio_data(pcm: "np.ndarray", sample_rate: int) -> "sr.AudioData":
    """Convert sounddevice float32 recording to a SpeechRecognition AudioData object."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)          # 16-bit
        wf.setframerate(sample_rate)
        pcm_int16 = (np.clip(pcm, -1.0, 1.0) * 32767).astype(np.int16)
        wf.writeframes(pcm_int16.tobytes())
    wav_bytes = buf.getvalue()
    return sr.AudioData(wav_bytes, sample_rate, 2)


# ─────────────────────────────────────────────
# SpeechEngine
# ─────────────────────────────────────────────
class SpeechEngine:
    """
    Records audio via sounddevice and transcribes it with Google's free STT.

    No PyAudio, no API key required.

    Public API is identical to the previous implementation — no other file
    needs to change.

    Usage
    -----
    engine = SpeechEngine()
    text   = engine.listen()
    """

    def __init__(self, language: str = "English"):
        self.recognizer  = sr.Recognizer() if _SR_AVAILABLE else None
        self._language   = LANGUAGES.get(language, "en-IN")
        self._lock       = threading.Lock()
        self._calibrated = True
        self._mic_ok     = False

        if not _SD_AVAILABLE:
            logger.warning("sounddevice not installed. Voice features disabled.")
        elif not _SR_AVAILABLE:
            logger.warning("SpeechRecognition not installed. Voice features disabled.")
        else:
            self._init_mic()

        logger.info("SpeechEngine initialised. Language: %s", self._language)

    # ─────────────────────────────────────────
    def _init_mic(self):
        """Verify at least one mic input device is available."""
        try:
            devices = sd.query_devices()
            inputs  = [d for d in devices if d["max_input_channels"] > 0]
            if not inputs:
                raise MicrophoneNotFoundError("No microphone devices found.")
            self._mic_ok = True
            logger.debug("Microphone detected: %s", inputs[0]["name"])
        except Exception as exc:
            logger.error("Microphone init error: %s", exc)
            self._mic_ok = False

    # ─────────────────────────────────────────
    # Calibrate (no-op — kept for API compat)
    # ─────────────────────────────────────────
    def calibrate(self, duration: float = 1.5):
        """No-op. sounddevice doesn't need separate noise calibration."""
        logger.debug("calibrate() called (no-op for sounddevice backend).")

    # ─────────────────────────────────────────
    # Core listen
    # ─────────────────────────────────────────
    def listen(
        self,
        timeout: int      = None,
        phrase_limit: int = None,
        retries: int      = None,
    ) -> str:
        """
        Record audio and return Google-transcribed text (free, no key).

        Parameters
        ----------
        timeout      : int  Unused (kept for API compat).
        phrase_limit : int  Seconds to record (overrides SR_RECORD_SECONDS).
        retries      : int  Number of retries on recognition failure.

        Returns
        -------
        str  Recognised text (lowercase, stripped).

        Raises
        ------
        MicrophoneNotFoundError
        SpeechRecognitionError
        """
        if not self._mic_ok:
            raise MicrophoneNotFoundError("Microphone not available.")
        if not self._SR_ready:
            raise SpeechRecognitionError("SpeechRecognition not available.")

        record_secs = phrase_limit or SR_RECORD_SECONDS
        max_retries = retries      or SR_MAX_RETRIES

        last_error = None
        for attempt in range(1, max_retries + 1):
            logger.debug("Listen attempt %d/%d (%.1fs)", attempt, max_retries, record_secs)
            try:
                # ── 1. Record via sounddevice ────────────────────────────
                with self._lock:
                    logger.debug("Recording %.1f s at %d Hz…", record_secs, SR_SAMPLE_RATE)
                    pcm = sd.rec(
                        int(record_secs * SR_SAMPLE_RATE),
                        samplerate=SR_SAMPLE_RATE,
                        channels=1,
                        dtype="float32",
                    )
                    sd.wait()
                    pcm = pcm.flatten()

                # ── 2. Wrap as SpeechRecognition AudioData ───────────────
                audio_data = _pcm_to_audio_data(pcm, SR_SAMPLE_RATE)

                # ── 3. Transcribe (free Google STT — no API key) ─────────
                text = self.recognizer.recognize_google(
                    audio_data, language=self._language
                )
                logger.info("Recognised: '%s'", text)
                return text.strip().lower()

            except sr.UnknownValueError:
                last_error = "Speech was not clear enough to recognise."
                logger.warning("UnknownValue on attempt %d.", attempt)

            except sr.RequestError as exc:
                last_error = f"Speech service error: {exc}"
                logger.error("RequestError on attempt %d: %s", attempt, exc)
                break   # no point retrying on network error

            except Exception as exc:
                last_error = str(exc)
                logger.error("Unexpected listen error on attempt %d: %s", attempt, exc)
                break

        raise SpeechRecognitionError(last_error or "Speech recognition failed.")

    # ─────────────────────────────────────────
    # Yes / No listener
    # ─────────────────────────────────────────
    def listen_for_confirmation(self) -> bool | None:
        """
        Listen for a Yes or No response.

        Returns
        -------
        True   → confirmed "yes"
        False  → confirmed "no"
        None   → could not determine
        """
        try:
            text = self.listen(phrase_limit=4, retries=2)
            yes_words = {"yes", "yeah", "yep", "correct", "right", "sure", "ok", "okay", "ha", "haan"}
            no_words  = {"no", "nope", "nahi", "wrong", "not", "nah", "nahin", "incorrect"}
            if any(w in text for w in yes_words):
                return True
            if any(w in text for w in no_words):
                return False
            logger.debug("Confirmation unclear: '%s'", text)
            return None
        except SpeechRecognitionError:
            return None

    # ─────────────────────────────────────────
    # Async callback listen
    # ─────────────────────────────────────────
    def listen_async(self, callback, timeout: int = None, phrase_limit: int = None):
        """
        Start listening in a background thread.

        Parameters
        ----------
        callback     : Callable[[str | None, Exception | None], None]
                       Called with (text, error) when done.
        timeout      : int  Unused (kept for API compat).
        phrase_limit : int  Seconds to record.
        """
        def _run():
            try:
                text = self.listen(timeout=timeout, phrase_limit=phrase_limit)
                callback(text, None)
            except (MicrophoneNotFoundError, SpeechRecognitionError) as exc:
                callback(None, exc)

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return t

    # ─────────────────────────────────────────
    # Language
    # ─────────────────────────────────────────
    def set_language(self, language_name: str):
        """
        Change the recognition language.

        Parameters
        ----------
        language_name : str  Key from config.LANGUAGES (e.g. 'Hindi').
        """
        lang_code = LANGUAGES.get(language_name)
        if lang_code:
            self._language = lang_code
            logger.info("Speech language set to: %s (%s)", language_name, lang_code)
        else:
            logger.warning(
                "Unknown language: %s. Available: %s",
                language_name, list(LANGUAGES.keys())
            )

    # ─────────────────────────────────────────
    # Availability check
    # ─────────────────────────────────────────
    @property
    def _SR_ready(self) -> bool:
        return _SR_AVAILABLE and self.recognizer is not None

    @property
    def is_available(self) -> bool:
        """Return True if speech recognition is fully operational."""
        return _SD_AVAILABLE and _SR_AVAILABLE and self._mic_ok

    @staticmethod
    def list_microphones() -> list[str]:
        """Return names of all available microphone devices."""
        try:
            devices = sd.query_devices()
            return [d["name"] for d in devices if d["max_input_channels"] > 0]
        except Exception as exc:
            logger.error("list_microphones error: %s", exc)
            return []
