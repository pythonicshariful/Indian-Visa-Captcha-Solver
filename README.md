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
└──────────────────────┘                          └─────────────────────────┘
```

## Solvers Overview

This project supports three different solvers. You can switch between them by editing `config.py`.

1. **EasyOCR (Default):** Runs locally using PyTorch. Highly accurate but might require an initial download of the English model. Does not require any external installation (other than `pip install`).
2. **Gemini API:** Uses Google's Gemini Vision model for perfect accuracy. Requires a free API key.
3. **Tesseract OCR:** A fast, local, traditional OCR engine. Requires installing Tesseract software on your machine.

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
ACTIVE_SOLVER = "easyocr"  # Options: "easyocr", "gemini", "tesseract"
```

- If using **Gemini**: You must set `GEMINI_API_KEY` in `config.py` to your Google AI Studio API key.
- If using **Tesseract**: You must install the Tesseract OCR executable for your operating system (e.g., from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) on Windows) and add it to your PATH.

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
| **Multi-Solver** | Choose between EasyOCR, Gemini AI, or Tesseract |
| **Image Preprocessing**| OpenCV cleans noise and removes strikethroughs automatically |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Server offline" | Make sure `python server.py` is running |
| "Tesseract not found" | If using Tesseract, install the `.exe` and add it to PATH |
| Captcha is incorrect | Ensure you are using `easyocr` or `gemini` in `config.py` for best accuracy |
| Input not filling | Check the Tampermonkey panel. If it says "Too short", it will automatically retry. |
