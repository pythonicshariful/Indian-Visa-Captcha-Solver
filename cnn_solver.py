"""
CNN Captcha Solver
==================
Solves captchas with the custom Keras CNN trained in the
`captcha-breaker-ml` project (GeeksforGeeks "Breaking a CAPTCHA system
with Machine Learning" architecture):

    Input 200x50 grayscale -> Conv2D(32) -> MaxPool -> Conv2D(64) -> MaxPool
    -> Flatten -> Dense(128) -> 5 softmax heads (one per character)

Model facts (verified on a held-out test set, 2026-10-30):
- Expects EXACTLY 5 characters, charset a-z + 0-9 (lowercase output)
- Trained on the Captcha-v2 dataset (1,040 images, 940 train / 100 test)
- Per-char accuracy 54.4%, full-captcha exact match 5% on held-out data
- The training dataset only contains 19 unique characters
  (2 3 4 5 6 7 8 b c d e f g m n p w x y), so other characters
  cannot be recognised reliably.
- It was NOT trained on Indian Visa captchas — expect poor results on
  the visa site until it is retrained on visa-style captcha images.

Place the trained file at models/captcha_model.keras (see models/README.md).
"""

import logging
import os
import string

import numpy as np
from PIL import Image

log = logging.getLogger("captcha-solver")

IMG_WIDTH = 200
IMG_HEIGHT = 50
NUM_CHARS = 5
CHAR_SET = string.ascii_lowercase + string.digits

_model = None
_model_error = None


def _load_model(model_path: str):
    """Lazy-load the Keras model once."""
    global _model, _model_error
    if _model is not None or _model_error is not None:
        return _model
    try:
        import tensorflow as tf  # heavy import — only when CNN solver is used

        if not os.path.exists(model_path):
            _model_error = f"CNN model file not found: {model_path}"
            log.error(_model_error)
            return None
        _model = tf.keras.models.load_model(model_path, compile=False)
        log.info(f"CNN model loaded: {model_path}")
    except Exception as e:  # tensorflow missing or model unreadable
        _model_error = f"Could not load CNN model: {e}"
        log.error(_model_error)
    return _model


def solve_captcha_cnn(img: Image.Image, model_path: str) -> dict:
    """Solve captcha using the custom CNN model. Same result shape as
    the other solvers: {text, confidence, all_results, solver}."""
    model = _load_model(model_path)
    if model is None:
        return {"text": "", "confidence": 0, "all_results": [],
                "solver": "cnn", "error": _model_error or "model unavailable"}
    try:
        import cv2

        gray = np.array(img.convert("L"))
        resized = cv2.resize(gray, (IMG_WIDTH, IMG_HEIGHT))
        x = (resized.astype("float32") / 255.0).reshape(1, IMG_HEIGHT, IMG_WIDTH, 1)

        preds = model.predict(x, verbose=0)
        chars, probs = [], []
        for head in preds:
            idx = int(np.argmax(head[0]))
            chars.append(CHAR_SET[idx])
            probs.append(float(head[0][idx]))
        text = "".join(chars)
        confidence = round(float(np.mean(probs)) * 100, 1)
        return {"text": text, "confidence": confidence,
                "all_results": [text], "solver": "cnn"}
    except Exception as e:
        log.error(f"CNN solver error: {e}")
        return {"text": "", "confidence": 0, "all_results": [],
                "solver": "cnn", "error": str(e)}
