"""
validators.py
Shared input checks and small helpers used by the Task and Schedule classes.
Dates are stored as YYYY-MM-DD and times as 24-hour HH:MM so they sort correctly.
"""

from datetime import datetime

CATEGORIES = ("School", "Personal", "Important", "Work", "Health")


def validate_title(value, label="Title"):
    """Return an error message, or None if the title is valid."""
    if not value or not value.strip():
        return f"{label} is required."
    if len(value.strip()) > 50:
        return f"{label} must be 50 characters or less."
    return None


def validate_date(value):
    """Return an error message, or None if the date is a real YYYY-MM-DD date."""
    if not value or not value.strip():
        return "Date is required."
    try:
        datetime.strptime(value.strip(), "%Y-%m-%d")
    except ValueError:
        return "Date must be a real date in YYYY-MM-DD format (example: 2026-11-05)."
    return None


def validate_time(value):
    """Return an error message, or None if the time is a real 24-hour HH:MM time."""
    if not value or not value.strip():
        return "Time is required."
    try:
        datetime.strptime(value.strip(), "%H:%M")
    except ValueError:
        return "Time must be in 24-hour HH:MM format (example: 14:30)."
    return None


def validate_category(value):
    if value not in CATEGORIES:
        return "Category must be one of: " + ", ".join(CATEGORIES) + "."
    return None


def normalize_date(value):
    """'2026-9-5' -> '2026-09-05' (call only after validate_date passes)."""
    return datetime.strptime(value.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")


def normalize_time(value):
    """'9:05' -> '09:05' (call only after validate_time passes)."""
    return datetime.strptime(value.strip(), "%H:%M").strftime("%H:%M")


def format_time_12h(value):
    """'13:00' -> '1:00 PM' for display on the screens."""
    try:
        return datetime.strptime(value, "%H:%M").strftime("%I:%M %p").lstrip("0")
    except (ValueError, TypeError):
        return value


def format_date_friendly(value):
    """'2026-11-02' -> 'Today' / 'Tomorrow' / 'Yesterday' / 'Nov 5' (adds the year if not this year)."""
    try:
        day = datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return value
    now = datetime.now().date()
    delta = (day - now).days
    if delta == 0:
        return "Today"
    if delta == 1:
        return "Tomorrow"
    if delta == -1:
        return "Yesterday"
    text = f"{day.strftime('%b')} {day.day}"
    return text if day.year == now.year else f"{text}, {day.year}"


def today_string():
    return datetime.now().strftime("%Y-%m-%d")


# Quick self-test: run this file directly
if __name__ == "__main__":
    print("1. Title empty      ->", validate_title(""))
    print("2. Title ok         ->", validate_title("Study"))
    print("3. Date bad         ->", validate_date("2026-02-31"))
    print("4. Date ok          ->", validate_date("2026-11-05"))
    print("5. Time bad         ->", validate_time("25:00"))
    print("6. Time ok          ->", validate_time("14:30"))
    print("7. Category bad     ->", validate_category("Fun"))
    print("8. Category ok      ->", validate_category("Health"))
    print("9. Normalize        ->", normalize_date("2026-9-5"), normalize_time("9:05"))
    print("10. 12-hour display ->", format_time_12h("13:00"), "|", format_time_12h("08:05"),
          "|", format_time_12h("00:30"))
    print("Validators OK.")