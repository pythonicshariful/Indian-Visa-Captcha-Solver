"""
Configuration settings for the Captcha Solver Server.
"""

import os

# Load variables from a local .env file if present (never commit .env to git).
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── General Settings ───────────────────────────────────────────────────────────
# Select which solver to use: "openrouter", "tesseract", "easyocr", or "cnn"
ACTIVE_SOLVER = "openrouter"

# ── CNN Solver Configuration ───────────────────────────────────────────────────
# Path of the trained Keras model used by the "cnn" solver
# (see cnn_solver.py and models/README.md). The .keras file itself is
# NOT stored in git — copy it into models/ yourself.
CNN_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "models", "captcha_model.keras"
)

# ── OpenRouter Solver Configuration ────────────────────────────────────────────
# Free vision-capable LLM OCR via OpenRouter (https://openrouter.ai).
# Create a free key at https://openrouter.ai/keys and set it as an env variable:
#   Windows:  setx OPENROUTER_API_KEY "your-key"
#   Linux:    export OPENROUTER_API_KEY="your-key"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Chat-completions endpoint and the vision model to use. The free router selects
# an available vision-capable model and avoids hard-coding rotating model IDs.
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openrouter/free"
