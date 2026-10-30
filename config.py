"""
Configuration settings for the Captcha Solver Server.
"""

import os

# ── General Settings ───────────────────────────────────────────────────────────
# Select which solver to use: "gemini", "tesseract", "easyocr", or "cnn"
ACTIVE_SOLVER = "easyocr"

# ── Gemini Configuration ───────────────────────────────────────────────────────
# Set your key as an environment variable — never commit a real key:
#   Windows:  setx GEMINI_API_KEY "your-key"
#   Linux:    export GEMINI_API_KEY="your-key"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ── CNN Solver Configuration ───────────────────────────────────────────────────
# Path of the trained Keras model used by the "cnn" solver
# (see cnn_solver.py and models/README.md). The .keras file itself is
# NOT stored in git — copy it into models/ yourself.
CNN_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "models", "captcha_model.keras"
)
