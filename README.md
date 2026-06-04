# 🔓 Indian Visa Captcha Solver

A hybrid captcha solver for the Indian Visa Bangladesh registration site. Uses a **Tampermonkey userscript** (browser-side) + **local Python Flask server** (OCR engine).

## Architecture

```
┌──────────────────────┐       POST /solve        ┌─────────────────────────┐
│   Tampermonkey        │ ──── (base64 image) ───→ │   Python Flask Server   │
│   Userscript          │                          │   (127.0.0.1:5555)      │
│                       │ ←── { text, confidence } │                         │
│  • Extracts captcha   │                          │  • 5 preprocessing      │
│  • Auto-fills input   │                          │    strategies           │
│  • Floating UI panel  │                          │  • 4 Tesseract configs  │
│  • Auto-retry logic   │                          │  • Consensus voting     │
└──────────────────────┘                           └─────────────────────────┘
```

## Prerequisites

### 1. Install Tesseract OCR

**Windows (step-by-step):**

#### Step 1 — Download the installer
Go to: https://digi.bib.uni-mannheim.de/tesseract/

Download the latest **64-bit** installer. The file will be named something like:
```
tesseract-ocr-w64-setup-5.x.x.exe
```

#### Step 2 — Run the installer
1. Double-click the downloaded `.exe` file
2. Click **Next** through the setup wizard
3. On the **"Choose Install Location"** screen, keep the default path:
   ```
   C:\Program Files\Tesseract-OCR
   ```
4. Complete the installation

#### Step 3 — Add to Windows PATH
1. Press **Win + R**, type `sysdm.cpl`, press **Enter**
2. Go to the **Advanced** tab → click **Environment Variables**
3. Under **System variables**, find and select **Path** → click **Edit**
4. Click **New** and add:
   ```
   C:\Program Files\Tesseract-OCR
   ```
5. Click **OK** → **OK** → **OK** to save

#### Step 4 — Verify installation
> ⚠️ **Important:** Open a **new** PowerShell/CMD window (existing ones won't pick up the PATH change)

```bash
tesseract --version
```
You should see output like `tesseract v5.x.x`.

#### Alternative (skip PATH setup)
If you don't want to modify PATH, uncomment line 28 in `server.py` and hardcode the path:
```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### 2. Install Python Dependencies

```bash
cd d:\motin\capsolver
pip install -r requirements.txt
```

### 3. Install Tampermonkey Browser Extension

- [Chrome](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)
- [Firefox](https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/)
- [Edge](https://microsoftedge.microsoft.com/addons/detail/tampermonkey/iikmkjmpaadaobahmlepeloendndfphd)

## Quick Start

### Step 1: Start the Python server

```bash
cd d:\motin\capsolver
python server.py
```

You should see:
```
08:00:00 │ INFO    │ ════════════════════════════════════════════════════════════
08:00:00 │ INFO    │   CAPTCHA SOLVER SERVER
08:00:00 │ INFO    │   Listening on http://127.0.0.1:5555
08:00:00 │ INFO    │ ════════════════════════════════════════════════════════════
08:00:00 │ INFO    │   Tesseract version: 5.x.x
```

### Step 2: Install the Tampermonkey userscript

1. Open Tampermonkey Dashboard
2. Click **"+"** (Create new script)
3. Delete the template content
4. Paste the entire contents of `tampermonkey-captcha-solver.user.js`
5. Press **Ctrl+S** to save

### Step 3: Visit the site

Go to https://indianvisa-bangladesh.nic.in/visa/Registration

The floating panel will appear in the bottom-right corner and auto-solve the captcha.

## Features

| Feature | Description |
|---------|-------------|
| **Auto-solve** | Automatically solves captcha on page load |
| **Auto-fill** | Fills the captcha input field and triggers proper events |
| **Auto-retry** | If confidence is low, refreshes captcha and retries (up to 5x) |
| **Floating UI** | Shows solve status, confidence, and alternative results |
| **Multi-strategy OCR** | 5 image preprocessing pipelines × 4 Tesseract configs |
| **Consensus voting** | Multiple OCR results vote on the best answer |
| **CORS handling** | Uses `GM_xmlhttpRequest` to bypass CORS restrictions |

## Configuration

Edit the `CONFIG` object in the Tampermonkey script:

```javascript
const CONFIG = {
    SERVER_URL: "http://127.0.0.1:5555/solve",
    AUTO_SOLVE: true,          // Auto-solve on page load
    AUTO_FILL: true,           // Auto-fill input field
    AUTO_RETRY_ON_FAIL: true,  // Retry on low confidence
    MIN_CONFIDENCE: 30,        // Minimum confidence threshold %
    MAX_RETRIES: 5,            // Max retry attempts
};
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Server offline" | Make sure `python server.py` is running |
| "Tesseract not found" | Install Tesseract and add to PATH |
| Low accuracy | Try adjusting preprocessing thresholds in `server.py` |
| CORS errors | Make sure `@connect 127.0.0.1` is in the userscript header |
| Input not filling | Check `getCaptchaInput()` selectors in the userscript |
