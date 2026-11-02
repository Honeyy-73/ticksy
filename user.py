"""
user.py
The User class: handles registration, login, and logout.
Passwords are never stored as plain text. Each password is salted
and hashed with PBKDF2 before being saved in the database.
The login ID can be an email or a username (like the "Email / Username" field).
"""

import hashlib
import hmac
import os
import re

from database import Database


class User:
    """Represents the person using the app."""

    def __init__(self, db=None):
        self.db = db or Database()
        self.id = None
        self.username = None
        self.full_name = None

    # ---------- password helpers ----------
    @staticmethod
    def _hash_password(password, salt):
        """Return a hex hash of the password using the given salt."""
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000
        ).hex()

    # ---------- validation ----------
    @staticmethod
    def validate_registration(login_id, full_name, password, confirm_password):
        """Return an error message, or None if everything is valid.
        The checks run in the same order as the sign-up screen."""
        if not full_name or not full_name.strip():
            return "Please enter your full name."
        if not login_id or not login_id.strip():
            return "Please enter your email or username."

        login_id = login_id.strip()
        if "@" in login_id:
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", login_id):
                return "Please enter a valid email address."
        elif not re.fullmatch(r"[A-Za-z0-9_.\-]{3,30}", login_id):
            return "Username must be 3-30 characters (letters, numbers, . _ -)."

        if len(password) < 6:
            return "Password must be at least 6 characters."
        if password != confirm_password:
            return "Passwords do not match."
        return None

    # ---------- main features ----------
    def register(self, login_id, full_name, password, confirm_password):
        """Create a new account. Returns (success, message)."""
        login_id = (login_id or "").strip()
        full_name = (full_name or "").strip()

        error = self.validate_registration(login_id, full_name, password, confirm_password)
        if error:
            return False, error

        existing = self.db.fetch_one(
            "SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (login_id,)
        )
        if existing:
            return False, "That email or username is already registered."

        salt = os.urandom(16).hex()
        password_hash = self._hash_password(password, salt)
        self.db.execute(
            "INSERT INTO users (username, full_name, salt, password_hash) VALUES (?, ?, ?, ?)",
            (login_id, full_name, salt, password_hash),
        )
        return True, "Account created successfully."

    def login(self, login_id, password):
        """Check credentials. On success, remembers who is logged in."""
        login_id = (login_id or "").strip()
        if not login_id or not password:
            return False, "Please enter your email/username and password."

        row = self.db.fetch_one(
            "SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (login_id,)
        )
        if row is None:
            return False, "Invalid username/email or password."

        attempt = self._hash_password(password, row["salt"])
        if not hmac.compare_digest(attempt, row["password_hash"]):
            return False, "Invalid username/email or password."

        self.id = row["id"]
        self.username = row["username"]
        self.full_name = row["full_name"]
        return True, f"Welcome, {self.full_name}!"

    def logout(self):
        """Forget the logged-in user."""
        self.id = None
        self.username = None
        self.full_name = None

    def is_logged_in(self):
        return self.id is not None

    def first_name(self):
        """Used for the dashboard greeting."""
        return self.full_name.split()[0] if self.full_name else ""


# Quick self-test: run this file directly
if __name__ == "__main__":
    test_db = Database("test_user_check.db")
    user = User(test_db)

    print("1. Empty fields     ->", user.register("", "", "", ""))
    print("2. No full name     ->", user.register("symon", "", "secret1", "secret1"))
    print("3. Bad email        ->", user.register("symon@gmail", "Symon Cortez", "secret1", "secret1"))
    print("4. Short password   ->", user.register("symon", "Symon Cortez", "123", "123"))
    print("5. Mismatch         ->", user.register("symon", "Symon Cortez", "secret1", "secret2"))
    print("6. Register email   ->", user.register("symon@gmail.com", "Symon Cortez", "secret1", "secret1"))
    print("7. Duplicate (case) ->", user.register("SYMON@gmail.com", "Another", "secret1", "secret1"))
    print("   Register username->", user.register("maria_s", "Maria Santos", "secret2", "secret2"))
    print("8. Wrong password   ->", user.login("symon@gmail.com", "wrongpass"))
    print("   Unknown user     ->", user.login("nobody", "secret1"))
    print("9. Correct login    ->", user.login("symon@gmail.com", "secret1"))
    print("   Logged in?       ->", user.is_logged_in(), "| first name =", user.first_name())
    user.logout()
    print("   After logout     ->", user.is_logged_in())
    print("   Login by username->", user.login("maria_s", "secret2"))

    stored = test_db.fetch_one("SELECT password_hash FROM users WHERE id = 1")
    print("10. Stored password ->", stored["password_hash"][:20], "... (hashed)")

    os.remove(test_db.db_path)
    print("User OK - test database removed.")