# 🔓 Indian Visa Captcha Solver

A hybrid captcha solver for the Indian Visa Bangladesh registration site. Uses a **Tampermonkey userscript** (browser-side) + **local Python Flask server** (OCR engine).

## Architecture

```
┌──────────────────────┐       POST /solve        ┌─────────────────────────┐
│   Tampermonkey       │ ──── (base64 image) ───→ │   Python Flask Server   │
│   Userscript         │                          │   (127.0.0.1:5555)      │
│                      │ ←── { text, confidence } │                         │
│  • Extracts captcha  │                          │  • EasyOCR (Default)    │
│  • Auto-fills input  │                          │  • Gemini API           │
│  • Auto-retry logic  │                          │  • Tesseract OCR        │
│                      │                          │  • Custom CNN model     │
└──────────────────────┘                          └─────────────────────────┘
```

## Solvers Overview

This project supports four different solvers. You can switch between them by editing `config.py`.

1. **EasyOCR (Default):** Runs locally using PyTorch. Highly accurate but might require an initial download of the English model. Does not require any external installation (other than `pip install`).
2. **Gemini API:** Uses Google's Gemini Vision model for perfect accuracy. Requires a free API key.
3. **Tesseract OCR:** A fast, local, traditional OCR engine. Requires installing Tesseract software on your machine.
4. **Custom CNN (`cnn`):** A Keras CNN trained on the Captcha-v2 dataset (GeeksforGeeks "Breaking a CAPTCHA system" architecture, see `cnn_solver.py`). Fully local, no API key. ⚠️ Honest limits: it only handles **5-character** captchas, was NOT trained on Indian Visa captchas, and scored ~54% per-character / ~5% full-captcha on its own held-out test set — so on the visa site EasyOCR or Gemini will usually do better until the CNN is retrained on visa-style captcha images. Requires the model file at `models/captcha_model.keras` (not stored in git — see `models/README.md`) and TensorFlow installed. **Download the trained model:** [captcha_model.keras on Google Drive](https://drive.google.com/file/d/1jxr-zIRxLjDlbN1cPWebpR2NrvYsaTqA/view?usp=drivesdk) — save it into the `models/` folder. *(Note: the file is shared from the owner's Drive account; if the link asks for access, request it from the owner.)*

---

## Prerequisites

### 1. Install Python Dependencies

Open a terminal in the project directory and install the required Python packages:

```bash
pip install -r requirements.txt
```

*(Note: The first time you run the server with EasyOCR, it may take a minute to download the EasyOCR language models).*

### 2. Configure Your Solver (Optional)

Open `config.py` and set your preferred solver:

```python
ACTIVE_SOLVER = "easyocr"  # Options: "easyocr", "gemini", "tesseract", "cnn"
```

- If using **Gemini**: Set your Google AI Studio key as an environment variable — never paste it into `config.py` (this repo is public):
  - Windows: `setx GEMINI_API_KEY "your-key"` then restart the terminal
  - Linux/Mac: `export GEMINI_API_KEY="your-key"`
  - ⚠️ An earlier version of `config.py` contained a real key in plain text. That key is compromised — revoke it in Google AI Studio and issue a new one.
- If using **Tesseract**: You must install the Tesseract OCR executable for your operating system (e.g., from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) on Windows) and add it to your PATH.
- If using **CNN**: Copy the trained `captcha_model.keras` into the `models/` folder (see `models/README.md`) and make sure TensorFlow is installed (`pip install tensorflow`).

### 3. Install Tampermonkey Browser Extension

- [Chrome](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)
- [Firefox](https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/)
- [Edge](https://microsoftedge.microsoft.com/addons/detail/tampermonkey/iikmkjmpaadaobahmlepeloendndfphd)

---

## Quick Start

### Step 1: Start the Python server

```bash
python server.py
```

### Step 2: Install the Tampermonkey userscript

1. Open Tampermonkey Dashboard in your browser.
2. Click **"+"** (Create new script).
3. Delete the template content.
4. Paste the entire contents of `tampermonkey-captcha-solver.user.js`.
5. Press **Ctrl+S** to save.

### Step 3: Visit the site

Go to https://indianvisa-bangladesh.nic.in/visa/Registration

The floating panel will appear in the bottom-right corner and auto-solve the captcha!

## Features

| Feature | Description |
|---------|-------------|
| **Auto-solve** | Automatically solves captcha on page load |
| **Auto-fill** | Fills the captcha input field and triggers proper events |
| **Auto-retry** | Refreshes and retries if confidence is low or text is too short (< 5 chars) |
| **Multi-Solver** | Choose between EasyOCR, Gemini AI, Tesseract, or the custom CNN model |
| **Image Preprocessing**| OpenCV cleans noise and removes strikethroughs automatically |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Server offline" | Make sure `python server.py` is running |
| "Tesseract not found" | If using Tesseract, install the `.exe` and add it to PATH |
| Captcha is incorrect | Ensure you are using `easyocr` or `gemini` in `config.py` for best accuracy |
| Input not filling | Check the Tampermonkey panel. If it says "Too short", it will automatically retry. |
