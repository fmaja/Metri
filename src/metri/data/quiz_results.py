# src/metri/data/quiz_results.py - POPRAWIONY

import json
import os
from datetime import datetime

# Use a more robust path (e.g., in user's AppData), but for simplicity:
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
QUIZ_RESULTS_FILE = os.path.join(DATA_DIR, "quiz_results.json")


def _ensure_file():
    """Ensures the data directory and file exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(QUIZ_RESULTS_FILE):
        # Initial structure for all quizzes
        data = {
            "interval": [],
            "harmony": [],
            "rhythm": []
        }
        with open(QUIZ_RESULTS_FILE, "w") as f:
            json.dump(data, f, indent=4)


def save_session(quiz_type: str, session_data: dict):
    """
    Save one completed quiz session with a timestamp and flexible data.

    For "interval" or "harmony":
    session_data = {"correct": int, "wrong": int}

    For "rhythm":
    session_data = {"avg_error": float, "categories": {"perfect": int, "good": int, "mistake": int}}
    """
    _ensure_file()
    try:
        with open(QUIZ_RESULTS_FILE, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # Handle corrupted or missing JSON file
        data = {"interval": [], "harmony": [], "rhythm": []}

    if quiz_type not in data:
        data[quiz_type] = []

    # Add timestamp to the session data
    session_data["date"] = datetime.now().isoformat()

    data[quiz_type].append(session_data)

    try:
        with open(QUIZ_RESULTS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Error saving quiz results: {e}")


def get_last_sessions(quiz_type: str, max_sessions=5):
    """Return last N sessions for visualization."""
    _ensure_file()
    try:
        with open(QUIZ_RESULTS_FILE, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

    if quiz_type not in data:
        return []

    # Return the last 'max_sessions' items from the list
    return data[quiz_type][-max_sessions:]