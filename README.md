# 🔓 Indian Visa Captcha Solver

A hybrid captcha solver for the Indian Visa online application sites. A **Tampermonkey userscript** in your browser grabs the captcha image, sends it to a **local Python server** running on your own machine, and auto-fills the answer — no paid captcha service needed.

**Works out of the box in ~10 minutes.** Follow the Quick Start below exactly, step by step.

---

## How It Works

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

The server never leaves your machine (`127.0.0.1`). Only the Gemini solver (if you choose it) sends the captcha image to Google's API.

---

## Requirements

| What | Why |
|---|---|
| **Python 3.10 or newer** — [python.org](https://www.python.org/downloads/) (tick *"Add Python to PATH"* during install on Windows) | Runs the server |
| **A browser** (Chrome / Firefox / Edge) | Opens the visa site |
| **Tampermonkey extension** (free) | Runs the userscript |
| Extra items per solver | See Step 3 — each solver needs something different |

Supported sites (the userscript activates automatically only on these):

- https://indianvisa-bangladesh.nic.in/visa/*
- https://indianvisaonline.gov.in/visa/*

---

## Quick Start

### Step 1 — Download this project

Click **Code → Download ZIP** above and unzip it anywhere (e.g. `Documents\Indian-Visa-Captcha-Solver`), **or** use git:

```bash
git clone https://github.com/pythonicshariful/Indian-Visa-Captcha-Solver.git
cd Indian-Visa-Captcha-Solver
```

### Step 2 — Install Python packages

Open a terminal / Command Prompt **inside the project folder** and run:

```bash
pip install -r requirements.txt
```

> 💡 Recommended: use a virtual environment first —
> `python -m venv venv` then `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac).
>
> The full install includes some large packages (EasyOCR/PyTorch ~2 GB, TensorFlow ~600 MB). If disk space is a problem, install only what your chosen solver needs:
>
> | Solver | Install command |
> |---|---|
> | EasyOCR | `pip install flask flask-cors Pillow opencv-python numpy easyocr` |
> | Gemini | `pip install flask flask-cors Pillow opencv-python numpy` |
> | Tesseract | `pip install flask flask-cors Pillow opencv-python numpy pytesseract` + the Tesseract program (Step 3) |
> | CNN | `pip install flask flask-cors Pillow opencv-python numpy tensorflow` |

### Step 3 — Choose your solver

Open **`config.py`** and set one line:

```python
ACTIVE_SOLVER = "easyocr"   # ← change this
```

| Solver | Accuracy on visa captchas | Needs | Notes |
|---|---|---|---|
| `"easyocr"` ⭐ default | Good | Nothing extra | First run downloads its OCR model (~100 MB), then works fully offline |
| `"gemini"` | Best | Free Google AI Studio API key + internet | Sends the image to Google — see the key instructions below |
| `"tesseract"` | Fair | Tesseract program installed | Fastest, fully offline, but struggles with noisy captchas |
| `"cnn"` | Poor on visa captchas ⚠️ | Model file download (~51 MB) | A custom-trained model — see the honest warning below before choosing it |

**If you picked Gemini** — get a free key from [Google AI Studio](https://aistudio.google.com/apikey), then set it as an environment variable. **Never type the key into `config.py`** — this is a public repo and leaked keys get abused:

- Windows: open Command Prompt and run `setx GEMINI_API_KEY "your-key-here"`, then **close and reopen** the terminal
- Linux/Mac: `export GEMINI_API_KEY="your-key-here"` in the terminal where you start the server

**If you picked Tesseract (Windows)** — install the Tesseract program from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) and add its folder (usually `C:\Program Files\Tesseract-OCR`) to your PATH.

**If you picked CNN** —

1. Download the trained model: **[captcha_model.keras (Google Drive, ~51 MB)](https://drive.google.com/file/d/1jxr-zIRxLjDlbN1cPWebpR2NrvYsaTqA/view?usp=drivesdk)** (public link, no sign-in needed)
2. Put the file in the **`models/`** folder so the path is `models/captcha_model.keras`
3. Set `ACTIVE_SOLVER = "cnn"` in `config.py`

> ⚠️ **Honest warning about the CNN solver:** this model (a small Keras CNN from the GeeksforGeeks "Breaking a CAPTCHA system" tutorial) was trained on the *Captcha-v2* dataset, **not** on Indian Visa captchas. It only reads 5-character captchas, its training data contained just 19 different characters, and it scored ~54% per-character on its own test data. It is included for learning/experimenting — for real visa form work, **EasyOCR or Gemini will solve far more captchas correctly.**

### Step 4 — Start the server

In the same terminal, inside the project folder:

```bash
python server.py
```

You should see `Listening on http://127.0.0.1:5555`. Open that address in your browser — if a "Captcha Solver Server" page appears, the server is running. **Keep this terminal window open** while you use the solver.

Optional quick test (no website needed) — save any captcha image as `captcha.png` in the project folder and run:

```bash
curl -X POST -F "image=@captcha.png" http://127.0.0.1:5555/solve
```

You get back JSON like `{"text": "a3b9k", "confidence": 87.5, "solver": "easyocr", ...}`.

### Step 5 — Install the userscript

1. Install **Tampermonkey**: [Chrome](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo) · [Firefox](https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/) · [Edge](https://microsoftedge.microsoft.com/addons/detail/tampermonkey/iikmkjmpaadaobahmlepeloendndfphd)
2. Click the Tampermonkey icon → **Create a new script**
3. Delete the template text, then open **`tampermonkey-captcha-solver.user.js`** from this project, copy **all** of it, and paste it in
4. Press **Ctrl+S** to save

### Step 6 — Use it 🎉

1. Make sure `python server.py` is running
2. Go to the visa registration page: https://indianvisa-bangladesh.nic.in/visa/Registration
3. A panel appears in the **bottom-right corner** — it solves the captcha automatically and fills the answer box for you
4. If an answer is wrong or confidence is low, the script refreshes the captcha and retries by itself (up to 5 times)

---

## Userscript Settings

Open the userscript in Tampermonkey and edit the `CONFIG` block at the top:

| Setting | Default | What it does |
|---|---|---|
| `AUTO_SOLVE` | `true` | Solve automatically on page load |
| `AUTO_FILL` | `true` | Fill the answer box automatically |
| `AUTO_RETRY_ON_FAIL` | `true` | Refresh + retry when a result looks wrong |
| `MIN_CONFIDENCE` | `30` | Answers below this confidence % are rejected and retried |
| `MIN_LENGTH` | `5` | Answers shorter than this are rejected |
| `MAX_RETRIES` | `5` | How many times to retry before giving up |

---

## Project Structure

```
Indian-Visa-Captcha-Solver/
├── server.py                          ← Flask server (run this)
├── config.py                          ← Choose solver + settings
├── cnn_solver.py                      ← The custom CNN solver
├── requirements.txt                   ← Python packages
├── tampermonkey-captcha-solver.user.js ← Browser script (paste into Tampermonkey)
└── models/
    └── captcha_model.keras            ← You add this (Step 3, CNN only) — not in git
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Panel says **"Server offline"** | The Python server isn't running — start it with `python server.py` and keep the terminal open |
| `python` is not recognized | Python isn't in PATH — reinstall Python and tick *"Add Python to PATH"*, or use `py server.py` on Windows |
| **"Tesseract not found"** | Only affects the Tesseract solver — install the program (Step 3) or switch to `easyocr` |
| **"CNN model file not found"** | You selected `cnn` but `models/captcha_model.keras` is missing — download it (Step 3) into the `models/` folder |
| Gemini returns empty / error | The `GEMINI_API_KEY` environment variable isn't set in the terminal running the server — set it and restart the server (Step 3) |
| Captcha answers are often wrong | Switch solver in `config.py` — `gemini` is the most accurate, then `easyocr`. The `cnn` solver is expected to be weak on this site (see the warning in Step 3) |
| Panel doesn't appear on the site | Check Tampermonkey is enabled and the script is saved/on; the script only runs on the two visa domains listed above |
| First EasyOCR run is slow | Normal — it downloads its OCR model once (~100 MB), later runs are fast |
| Port 5555 already in use | Another copy of the server is running — close the old terminal, or change the port in `server.py` **and** `SERVER_URL`/`HEALTH_URL` in the userscript |

---

## FAQ

**Which solver should I use?**
Gemini for the highest accuracy (needs internet + a free key), EasyOCR for a fully offline setup. Tesseract is the lightest. CNN is an educational extra.

**Does it work on other websites?**
The server's `/solve` endpoint works with any captcha image, but the userscript only activates on the two Indian Visa domains above. Adding another site means editing the `@match` lines in the userscript.

**Is my data private?**
With EasyOCR, Tesseract and CNN everything runs on your own computer. With Gemini, the captcha image is sent to Google's API.

**Why isn't the CNN model file in this repo?**
It's a 51 MB binary; GitHub repos here keep code only. It is hosted on Google Drive instead (public link in Step 3).

---

## About the CNN Model

The `cnn` solver uses a Keras CNN built following the GeeksforGeeks article
*“Breaking a CAPTCHA system with Machine Learning”* (Conv2D 32 → MaxPool →
Conv2D 64 → MaxPool → Flatten → Dense 128 → five softmax character heads),
trained on the Kaggle **Captcha version 2** dataset (1,040 images,
200×50 px, 5 characters). Held-out test results: **54.4% per-character,
5% full-captcha exact match** — reported honestly so you can choose the
right solver for the job.

---

## Disclaimer

This project is for **educational purposes and personal use** — for example, filling your own visa application faster. Automated solving may conflict with the target website's terms of use; you are responsible for how you use it.
