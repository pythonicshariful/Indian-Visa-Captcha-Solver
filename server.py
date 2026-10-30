"""
Captcha Solver Server
=====================
Local Flask server that receives captcha images and returns OCR results.
Optimized for Indian government website captchas (simple text/numbers with mild distortion).

Usage:
    python server.py

The server runs on http://127.0.0.1:5555
"""

import io
import base64
import re
import logging
import json
import urllib.request

import cv2
import config
from config import (
    ACTIVE_SOLVER,
    CNN_MODEL_PATH,
    OPENROUTER_API_KEY,
    OPENROUTER_URL,
    OPENROUTER_MODEL,
)
from cnn_solver import solve_captcha_cnn
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import pytesseract

try:
    import easyocr
    reader = easyocr.Reader(['en'])
except ImportError:
    reader = None

from flask import Flask, request, jsonify
from flask_cors import CORS

# ── Configure logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("captcha-solver")

# ── Flask app ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)  # Allow requests from Tampermonkey

# ── Tesseract path (uncomment & edit if tesseract is not on PATH) ──────────────
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ══════════════════════════════════════════════════════════════════════════════
#  IMAGE PREPROCESSING PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def preprocess_captcha(img: Image.Image) -> list[Image.Image]:
    """
    Apply multiple preprocessing strategies and return all variants.
    The OCR engine will try each and pick the best result.
    """
    variants = []

    # Convert to OpenCV format (BGR)
    img_cv = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)

    # ── Strategy 1: Grayscale → Otsu threshold ────────────────────────────────
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # Resize for better OCR (3x upscale)
    h, w = gray.shape
    gray_big = cv2.resize(gray, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)

    # Otsu binarization
    _, otsu = cv2.threshold(gray_big, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(Image.fromarray(otsu))

    # ── Strategy 2: Adaptive threshold ────────────────────────────────────────
    adaptive = cv2.adaptiveThreshold(
        gray_big, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
    )
    variants.append(Image.fromarray(adaptive))

    # ── Strategy 3: Aggressive noise removal with morphological ops ───────────
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray_big, h=30)
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Remove thin lines (captcha lines/scratches)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=1)
    variants.append(Image.fromarray(cleaned))

    # ── Strategy 4: Invert + clean (for dark background captchas) ─────────────
    inverted = cv2.bitwise_not(gray_big)
    _, inv_bin = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(Image.fromarray(inv_bin))

    # ── Strategy 5: PIL-based sharpening + high contrast ──────────────────────
    pil_big = img.convert("L").resize((w * 3, h * 3), Image.LANCZOS)
    pil_big = ImageEnhance.Contrast(pil_big).enhance(3.0)
    pil_big = ImageEnhance.Sharpness(pil_big).enhance(2.0)
    pil_big = pil_big.point(lambda x: 0 if x < 140 else 255)
    variants.append(pil_big)

    return variants


def clean_ocr_text(raw: str) -> str:
    """Clean OCR output — keep only alphanumeric characters."""
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", raw.strip())
    return cleaned


def extract_openrouter_text(content) -> str:
    """Extract assistant text from string or multimodal content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return " ".join(parts)
    if isinstance(content, dict) and isinstance(content.get("text"), str):
        return content["text"]
    return ""


def ocr_single(img: Image.Image, config: str) -> str:
    """Run Tesseract on a single image with given config."""
    try:
        text = pytesseract.image_to_string(img, config=config)
        return clean_ocr_text(text)
    except Exception:
        return ""


def solve_captcha(img: Image.Image) -> dict:
    """
    Try multiple preprocessing strategies and Tesseract configs.
    Return the best result (longest clean alphanumeric string).
    """
    variants = preprocess_captcha(img)

    # Tesseract configs to try
    configs = [
        # Standard single line mode, alphanumeric only
        "--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
        # Single word mode
        "--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
        # Treat as single line of text
        "--psm 13 --oem 3",
        # Single uniform block
        "--psm 6 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
    ]

    results = []
    for i, variant in enumerate(variants):
        for j, cfg in enumerate(configs):
            text = ocr_single(variant, cfg)
            if text:
                results.append({
                    "text": text,
                    "strategy": i,
                    "config": j,
                    "length": len(text),
                })

    if not results:
        return {"text": "", "confidence": 0, "all_results": []}

    # Indian gov captchas are typically 5-6 characters
    # Prefer results in that range, then pick longest
    ideal_range = [r for r in results if 4 <= r["length"] <= 7]
    pool = ideal_range if ideal_range else results

    # Deduplicate and count votes
    vote_count = {}
    for r in pool:
        t = r["text"]
        vote_count[t] = vote_count.get(t, 0) + 1

    # Pick the result with most votes (consensus)
    best_text = max(vote_count, key=vote_count.get)
    confidence = vote_count[best_text] / len(pool) * 100

    all_unique = list(set(r["text"] for r in results))

    return {
        "text": best_text,
        "confidence": round(confidence, 1),
        "all_results": all_unique[:10],
    }

def solve_captcha_easyocr(img: Image.Image) -> dict:
    """Solve captcha using EasyOCR."""
    if reader is None:
        return {"text": "", "confidence": 0, "all_results": [], "solver": "easyocr", "error": "EasyOCR not installed"}
        
    try:
        variants = preprocess_captcha(img)
        variants.insert(0, img) # include raw image
        
        results = []
        for variant in variants:
            img_np = np.array(variant.convert('RGB'))
            res = reader.readtext(img_np, detail=0)
            text = clean_ocr_text("".join(res))
            if text:
                results.append(text)
                
        if not results:
            return {"text": "", "confidence": 0, "all_results": [], "solver": "easyocr"}

        # Indian gov captchas are typically 5-6 characters
        ideal_range = [r for r in results if 4 <= len(r) <= 7]
        pool = ideal_range if ideal_range else results
        
        vote_count = {}
        for r in pool:
            vote_count[r] = vote_count.get(r, 0) + 1
            
        best_text = max(vote_count, key=vote_count.get)
        confidence = vote_count[best_text] / len(pool) * 100
        
        all_unique = list(set(results))
        
        return {
            "text": best_text,
            "confidence": round(confidence, 1),
            "all_results": all_unique[:10],
            "solver": "easyocr"
        }
    except Exception as e:
        log.error(f"EasyOCR error: {e}")
        return {"text": "", "confidence": 0, "all_results": [], "solver": "easyocr", "error": str(e)}


def solve_captcha_openrouter(img: Image.Image) -> dict:
    """
    Solve captcha using a free vision-capable LLM on OpenRouter.

    Approach adapted from https://github.com/ceodaniyal/free-llm-image-to-text:
    the image is sent as a base64 data URL to an OpenRouter chat-completions
    endpoint with a vision model. Here we send the raw image plus two
    preprocessed variants (strikethrough removed + high contrast) to help the
    model see past the noise on Indian government captchas.
    """
    if not OPENROUTER_API_KEY:
        return {"text": "", "confidence": 0, "all_results": [], "solver": "openrouter",
                "error": "OpenRouter API key not configured (set OPENROUTER_API_KEY)"}

    try:
        variants = preprocess_captcha(img)
        # variants[2] = strikethrough/noise removed, variants[4] = high contrast
        images = [img.convert("RGB"), variants[2].convert("RGB"), variants[4].convert("RGB")]

        content = [{
            "type": "text",
            "text": ("Solve the captcha shown in the images. It always contains exactly "
                     "5 or 6 alphanumeric characters — read them left to right. The "
                     "strikethrough lines are distractors; ignore them. Output ONLY the "
                     "captcha characters, with no explanation."),
        }]
        for im in images:
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            })

        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0.0,
            "max_tokens": 150,
            "reasoning": {"effort": "none", "exclude": True},
        }

        req = urllib.request.Request(
            OPENROUTER_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))

        choices = result.get("choices", [])
        message = choices[0].get("message", {}) if choices else {}
        raw_text = extract_openrouter_text(message.get("content", ""))
        text = clean_ocr_text(raw_text or "")
        if not text:
            finish_reason = choices[0].get("finish_reason") if choices else None
            log.warning(
                "OpenRouter returned no OCR text (model=%s, finish_reason=%s, message_keys=%s)",
                result.get("model", OPENROUTER_MODEL),
                finish_reason,
                sorted(message.keys()) if isinstance(message, dict) else [],
            )
            return {
                "text": "", "confidence": 0, "all_results": [],
                "solver": "openrouter",
                "error": "OpenRouter returned no readable text",
            }

        return {
            "text": text,
            "confidence": 100.0 if text else 0,
            "all_results": [text] if text else [],
            "solver": "openrouter",
        }
    except urllib.error.HTTPError as e:
        response_body = e.read().decode("utf-8", errors="replace").strip()
        error = f"OpenRouter HTTP {e.code}: {response_body or e.reason}"
        log.error(error)
        return {"text": "", "confidence": 0, "all_results": [], "solver": "openrouter", "error": error}
    except Exception as e:
        log.error(f"OpenRouter API error: {e}")
        return {"text": "", "confidence": 0, "all_results": [], "solver": "openrouter", "error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
#  API ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/solve", methods=["POST"])
def solve():
    """
    Accepts captcha image as:
      - base64 string in JSON body: {"image": "data:image/png;base64,..."}
      - raw image file upload:      form-data field "image"
    """
    try:
        if request.is_json:
            data = request.get_json()
            image_data = data.get("image", "")

            # Strip data URI prefix if present
            if "," in image_data:
                image_data = image_data.split(",", 1)[1]

            img_bytes = base64.b64decode(image_data)
            img = Image.open(io.BytesIO(img_bytes))
        elif "image" in request.files:
            img = Image.open(request.files["image"])
        else:
            return jsonify({"error": "No image provided"}), 400

        log.info(f"Received captcha image: {img.size[0]}x{img.size[1]}")
        
        # Use the solver configured in config.py
        solver = ACTIVE_SOLVER
        log.info(f"Using solver: {solver}")
        
        if solver == "cnn":
            result = solve_captcha_cnn(img, CNN_MODEL_PATH)
        elif solver == "openrouter":
            result = solve_captcha_openrouter(img)
        elif solver == "easyocr":
            result = solve_captcha_easyocr(img)
        elif solver == "tesseract":
            result = solve_captcha(img)
            result["solver"] = "tesseract"
        else:
            log.warning(f"Unknown solver '{solver}', falling back to Tesseract")
            result = solve_captcha(img)
            result["solver"] = "tesseract"

        # Log the result clearly
        if "error" in result:
            log.error(f"Solver error: {result['error']}")
        else:
            log.info(f"SOLVED CAPTCHA: '{result.get('text', '')}' (Confidence: {result.get('confidence', 0)}%)")

        return jsonify(result)

    except Exception as e:
        log.error(f"Error solving captcha: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    # Verify Tesseract is accessible
    try:
        version = pytesseract.get_tesseract_version()
        return jsonify({
            "status": "ok",
            "tesseract_version": str(version),
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Tesseract not found: {e}",
        }), 500


@app.route("/", methods=["GET"])
def index():
    """Landing page with status info."""
    return """
    <html>
    <head><title>Captcha Solver Server</title></head>
    <body style="font-family: monospace; background: #1a1a2e; color: #e0e0e0; padding: 40px;">
        <h1 style="color: #00d4ff;">🔓 Captcha Solver Server</h1>
        <p>Server is running. Use the Tampermonkey userscript to auto-solve captchas.</p>
        <h3>Endpoints:</h3>
        <ul>
            <li><code>POST /solve</code> — Send captcha image (base64 or file upload). The solver is chosen by <code>ACTIVE_SOLVER</code> in config.py: openrouter, tesseract, easyocr or cnn.</li>
            <li><code>GET /health</code> — Check Tesseract availability</li>
        </ul>
    </body>
    </html>
    """


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    log.info("=" * 60)
    log.info("  CAPTCHA SOLVER SERVER")
    log.info(f"  Active Solver: {ACTIVE_SOLVER}")
    log.info("  Listening on http://127.0.0.1:5555")
    log.info("=" * 60)

    # Check Tesseract on startup
    try:
        ver = pytesseract.get_tesseract_version()
        log.info(f"  Tesseract version: {ver}")
    except Exception as e:
        log.warning(f"  ⚠ Tesseract not found! Install it first.")
        log.warning(f"    Error: {e}")
        log.warning(f"    Download: https://github.com/UB-Mannheim/tesseract/wiki")

    # Check CNN model if active
    if ACTIVE_SOLVER == "cnn":
        import os
        if not os.path.exists(CNN_MODEL_PATH):
            log.warning(f"  ⚠ CNN model file not found at: {CNN_MODEL_PATH}")
            log.warning(f"    Please download it from the link in models/README.md")

    # Check OpenRouter key if active
    if ACTIVE_SOLVER == "openrouter" and not OPENROUTER_API_KEY:
        log.warning(f"  ⚠ OPENROUTER_API_KEY is not set")
        log.warning(f"    Get a free key at https://openrouter.ai/keys")
        log.warning(f"    Windows:  setx OPENROUTER_API_KEY \"your-key\"  (then restart)")

    app.run(host="127.0.0.1", port=5555, debug=False)
