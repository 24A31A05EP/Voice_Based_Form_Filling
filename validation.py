"""
validation.py — Input validators for the Voice Form Filling System.
Each validator returns a (is_valid: bool, message: str) tuple.
"""

import re
import logging

logger = logging.getLogger(__name__)


class Validator:
    """
    Validates all form fields.

    Usage
    -----
    v = Validator()
    ok, msg = v.validate_name("John Doe")
    """

    # ─────────────────────────────────────────
    # Name
    # ─────────────────────────────────────────
    @staticmethod
    def validate_name(name: str) -> tuple[bool, str]:
        """
        Name must contain only letters and spaces, at least 2 characters.
        """
        name = name.strip()
        if not name:
            return False, "Name cannot be empty."
        if len(name) < 2:
            return False, "Name must be at least 2 characters long."
        if not re.fullmatch(r"[A-Za-z\s\.\-']+", name):
            return False, "Name must contain letters only (no digits or special characters)."
        return True, ""

    # ─────────────────────────────────────────
    # Age
    # ─────────────────────────────────────────
    @staticmethod
    def validate_age(age: str) -> tuple[bool, str]:
        """
        Age must be a numeric value between 1 and 120.
        Accepts spoken forms like 'twenty five' by attempting digit extraction.
        """
        age = age.strip()
        if not age:
            return False, "Age cannot be empty."

        # Strip non-digit characters that may come from speech (e.g., "25 years")
        digits_only = re.sub(r"[^\d]", "", age)
        if not digits_only:
            return False, "Please provide a numeric age."
        try:
            age_int = int(digits_only)
        except ValueError:
            return False, "Age must be a valid number."

        if not (1 <= age_int <= 120):
            return False, f"Age must be between 1 and 120 (received {age_int})."
        return True, ""

    # ─────────────────────────────────────────
    # Gender
    # ─────────────────────────────────────────
    @staticmethod
    def validate_gender(gender: str) -> tuple[bool, str]:
        """
        Gender must be Male, Female, or Other (case-insensitive).
        """
        gender = gender.strip().lower()
        if not gender:
            return False, "Gender cannot be empty."
        valid = {"male", "female", "other", "m", "f", "o"}
        if gender not in valid:
            return False, "Gender must be Male, Female, or Other."
        return True, ""

    # ─────────────────────────────────────────
    # Phone
    # ─────────────────────────────────────────
    @staticmethod
    def validate_phone(phone: str) -> tuple[bool, str]:
        """
        Phone must be exactly 10 digits (Indian format).
        Strips spaces, hyphens, and the +91 prefix if present.
        """
        phone = phone.strip()
        if not phone:
            return False, "Mobile number cannot be empty."

        # Remove spaces, hyphens, dots, and country code
        cleaned = re.sub(r"[\s\-\.\(\)]+", "", phone)
        cleaned = re.sub(r"^\+91|^0091|^91", "", cleaned)

        if not cleaned.isdigit():
            return False, "Mobile number must contain digits only."
        if len(cleaned) != 10:
            return False, f"Mobile number must be exactly 10 digits (received {len(cleaned)})."
        if cleaned[0] not in "6789":
            return False, "Mobile number must start with 6, 7, 8, or 9."
        return True, ""

    # ─────────────────────────────────────────
    # Email
    # ─────────────────────────────────────────
    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """
        Validate email using a standard regex pattern.
        """
        email = email.strip().lower()
        if not email:
            return False, "Email address cannot be empty."
        pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            return False, "Please enter a valid email address (e.g. user@example.com)."
        return True, ""

    # ─────────────────────────────────────────
    # Address
    # ─────────────────────────────────────────
    @staticmethod
    def validate_address(address: str) -> tuple[bool, str]:
        """
        Address must have at least 10 characters.
        """
        address = address.strip()
        if not address:
            return False, "Address cannot be empty."
        if len(address) < 10:
            return False, f"Address must be at least 10 characters long (received {len(address)})."
        return True, ""

    # ─────────────────────────────────────────
    # Occupation
    # ─────────────────────────────────────────
    @staticmethod
    def validate_occupation(occupation: str) -> tuple[bool, str]:
        """
        Occupation must be at least 2 characters.
        """
        occupation = occupation.strip()
        if not occupation:
            return False, "Occupation cannot be empty."
        if len(occupation) < 2:
            return False, "Occupation must be at least 2 characters."
        return True, ""

    # ─────────────────────────────────────────
    # Validate entire form dict
    # ─────────────────────────────────────────
    def validate_all(self, data: dict) -> dict[str, str]:
        """
        Validate a full form data dictionary.

        Parameters
        ----------
        data : dict
            Keys: name, age, gender, phone, email, address, occupation

        Returns
        -------
        dict
            Field → error message (only for invalid fields).
            Empty dict means all valid.
        """
        errors = {}
        checks = {
            "name":       self.validate_name,
            "age":        self.validate_age,
            "gender":     self.validate_gender,
            "phone":      self.validate_phone,
            "email":      self.validate_email,
            "address":    self.validate_address,
            "occupation": self.validate_occupation,
        }
        for field, fn in checks.items():
            value = data.get(field, "")
            ok, msg = fn(str(value))
            if not ok:
                errors[field] = msg
                logger.debug("Validation failed for '%s': %s", field, msg)
        return errors

    # ─────────────────────────────────────────
    # Normalise helpers (clean speech output)
    # ─────────────────────────────────────────
    @staticmethod
    def normalise_gender(text: str) -> str:
        """Map spoken gender variants to Male/Female/Other."""
        t = text.strip().lower()
        if t in ("male", "m", "man", "boy", "he"):
            return "Male"
        if t in ("female", "f", "woman", "girl", "she"):
            return "Female"
        if t in ("other", "o", "non-binary", "nonbinary", "prefer not to say"):
            return "Other"
        return text.strip().capitalize()

    @staticmethod
    def normalise_age(text: str) -> str:
        """Extract digit string from age speech (e.g. '25 years old' → '25')."""
        digits = re.sub(r"[^\d]", "", text.strip())
        return digits if digits else text.strip()

    @staticmethod
    def normalise_phone(text: str) -> str:
        """Strip non-digit chars (and optional country code) from phone text."""
        cleaned = re.sub(r"[\s\-\.\(\)]+", "", text.strip())
        cleaned = re.sub(r"^\+91|^0091|^91", "", cleaned)
        return cleaned

    @staticmethod
    def normalise_email(text: str) -> str:
        """
        Fix common speech-to-text email artefacts:
        'at the rate' → '@', 'dot' → '.', 'underscore' → '_'
        """
        t = text.strip().lower()
        replacements = [
            (r"\bat the rate\b",  "@"),
            (r"\bat\b",           "@"),
            (r"\bdot\b",          "."),
            (r"\bunder score\b",  "_"),
            (r"\bunderscore\b",   "_"),
            (r"\bunder_score\b",  "_"),
            (r"\bhyphen\b",       "-"),
            (r"\bdash\b",         "-"),
            (r"\bspace\b",        ""),
            (r"\s+",              ""),   # remove all spaces
        ]
        for pattern, replacement in replacements:
            t = re.sub(pattern, replacement, t)
        return t
