// ==UserScript==
// @name         Indian Visa Captcha Auto-Solver
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Auto-solves captcha on Indian Visa Bangladesh registration page using local OCR server
// @author       CAPSolver
// @match        https://indianvisa-bangladesh.nic.in/visa/*
// @match        https://indianvisaonline.gov.in/visa/*
// @grant        GM_xmlhttpRequest
// @grant        GM_addStyle
// @connect      127.0.0.1
// @run-at       document-idle
// ==/UserScript==

(function () {
    "use strict";

    // ═══════════════════════════════════════════════════════════════════════════
    //  CONFIGURATION
    // ═══════════════════════════════════════════════════════════════════════════

    const CONFIG = {
        SERVER_URL: "http://127.0.0.1:5555/solve",
        HEALTH_URL: "http://127.0.0.1:5555/health",
        AUTO_SOLVE: true,          // Automatically solve on page load
        AUTO_FILL: true,           // Automatically fill the captcha input field
        AUTO_RETRY_ON_FAIL: true,  // Refresh captcha and retry if OCR confidence is low
        MIN_CONFIDENCE: 30,        // Minimum confidence % to accept result
        RETRY_DELAY_MS: 500,       // Delay before retrying
        MAX_RETRIES: 5,            // Maximum retry attempts
    };

    let retryCount = 0;
    let isSolving = false;

    // ═══════════════════════════════════════════════════════════════════════════
    //  FLOATING UI PANEL
    // ═══════════════════════════════════════════════════════════════════════════

    GM_addStyle(`
        #cap-solver-panel {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 300px;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 12px;
            padding: 16px;
            z-index: 99999;
            font-family: 'Segoe UI', system-ui, sans-serif;
            color: #e0e0e0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6), 0 0 20px rgba(0, 212, 255, 0.1);
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }
        #cap-solver-panel:hover {
            border-color: rgba(0, 212, 255, 0.6);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6), 0 0 30px rgba(0, 212, 255, 0.2);
        }
        #cap-solver-panel .title {
            font-size: 14px;
            font-weight: 700;
            color: #00d4ff;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        #cap-solver-panel .status {
            font-size: 12px;
            color: #aaa;
            margin-bottom: 8px;
            min-height: 18px;
        }
        #cap-solver-panel .result {
            font-size: 22px;
            font-weight: 700;
            color: #00ff88;
            text-align: center;
            padding: 8px;
            background: rgba(0, 255, 136, 0.08);
            border-radius: 8px;
            margin: 8px 0;
            letter-spacing: 4px;
            min-height: 34px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        #cap-solver-panel .confidence {
            font-size: 11px;
            text-align: center;
            color: #888;
        }
        #cap-solver-panel .btn-row {
            display: flex;
            gap: 6px;
            margin-top: 10px;
        }
        #cap-solver-panel .btn {
            flex: 1;
            padding: 8px;
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 6px;
            background: rgba(0, 212, 255, 0.1);
            color: #00d4ff;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            text-align: center;
            transition: all 0.2s;
        }
        #cap-solver-panel .btn:hover {
            background: rgba(0, 212, 255, 0.25);
            border-color: rgba(0, 212, 255, 0.6);
        }
        #cap-solver-panel .btn.refresh {
            color: #ffaa00;
            border-color: rgba(255, 170, 0, 0.3);
            background: rgba(255, 170, 0, 0.1);
        }
        #cap-solver-panel .btn.refresh:hover {
            background: rgba(255, 170, 0, 0.25);
        }
        #cap-solver-panel .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }
        #cap-solver-panel .dot.green { background: #00ff88; box-shadow: 0 0 6px #00ff88; }
        #cap-solver-panel .dot.red { background: #ff4444; box-shadow: 0 0 6px #ff4444; }
        #cap-solver-panel .dot.yellow { background: #ffaa00; box-shadow: 0 0 6px #ffaa00; animation: pulse 1s infinite; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }
        #cap-solver-panel .alt-results {
            font-size: 10px;
            color: #666;
            text-align: center;
            margin-top: 4px;
        }
    `);

    function createPanel() {
        const panel = document.createElement("div");
        panel.id = "cap-solver-panel";
        panel.innerHTML = `
            <div class="title">
                <span class="dot yellow" id="cap-status-dot"></span>
                🔓 Captcha Solver
            </div>
            <div class="status" id="cap-status">Initializing...</div>
            <div class="result" id="cap-result">—</div>
            <div class="confidence" id="cap-confidence"></div>
            <div class="alt-results" id="cap-alts"></div>
            <div class="btn-row">
                <div class="btn" id="cap-btn-solve">⚡ Solve</div>
                <div class="btn refresh" id="cap-btn-refresh">🔄 New Captcha</div>
            </div>
        `;
        document.body.appendChild(panel);

        document.getElementById("cap-btn-solve").addEventListener("click", () => {
            retryCount = 0;
            solveCaptcha();
        });
        document.getElementById("cap-btn-refresh").addEventListener("click", () => {
            retryCount = 0;
            refreshCaptcha();
        });
    }

    function setStatus(msg, dotClass = "yellow") {
        const statusEl = document.getElementById("cap-status");
        const dotEl = document.getElementById("cap-status-dot");
        if (statusEl) statusEl.textContent = msg;
        if (dotEl) {
            dotEl.className = "dot " + dotClass;
        }
    }

    function setResult(text, confidence, alts = []) {
        const resultEl = document.getElementById("cap-result");
        const confEl = document.getElementById("cap-confidence");
        const altsEl = document.getElementById("cap-alts");
        if (resultEl) resultEl.textContent = text || "—";
        if (confEl) confEl.textContent = confidence ? `Confidence: ${confidence}%` : "";
        if (altsEl) {
            const others = alts.filter((a) => a !== text).slice(0, 4);
            altsEl.textContent = others.length ? `Alternatives: ${others.join(", ")}` : "";
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    //  CAPTCHA IMAGE EXTRACTION
    // ═══════════════════════════════════════════════════════════════════════════

    function getCaptchaImage() {
        // Try by ID first
        let img = document.getElementById("capt");
        if (img) return img;

        // Fallback: find img whose src contains "captcha"
        const images = document.querySelectorAll('img[src*="captcha"]');
        if (images.length > 0) return images[0];

        return null;
    }

    function imageToBase64(imgElement) {
        return new Promise((resolve, reject) => {
            // Create a canvas and draw the image
            const canvas = document.createElement("canvas");
            canvas.width = imgElement.naturalWidth || imgElement.width;
            canvas.height = imgElement.naturalHeight || imgElement.height;

            const ctx = canvas.getContext("2d");
            ctx.drawImage(imgElement, 0, 0);

            try {
                const dataURL = canvas.toDataURL("image/png");
                resolve(dataURL);
            } catch (e) {
                // CORS issue — fetch the image via GM_xmlhttpRequest
                fetchImageAsBase64(imgElement.src).then(resolve).catch(reject);
            }
        });
    }

    function fetchImageAsBase64(url) {
        return new Promise((resolve, reject) => {
            // Make the URL absolute if relative
            const absoluteUrl = new URL(url, window.location.href).href;

            GM_xmlhttpRequest({
                method: "GET",
                url: absoluteUrl,
                responseType: "blob",
                onload: (response) => {
                    const reader = new FileReader();
                    reader.onloadend = () => resolve(reader.result);
                    reader.onerror = reject;
                    reader.readAsDataURL(response.response);
                },
                onerror: reject,
            });
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    //  CAPTCHA INPUT FIELD DETECTION
    // ═══════════════════════════════════════════════════════════════════════════

    function getCaptchaInput() {
        // Common selectors for captcha input fields on Indian gov sites
        const selectors = [
            'input[name="captchaText"]',
            'input[name="captcha"]',
            'input[name="captchaInput"]',
            'input[name="CaptchaInputText"]',
            'input[name="cap"]',
            'input[id="captchaText"]',
            'input[id="captcha"]',
            'input[id="captcha_input"]',
            'input[placeholder*="captcha" i]',
            'input[placeholder*="security" i]',
            'input[placeholder*="code" i]',
            'input[placeholder*="Enter" i]',
        ];

        for (const sel of selectors) {
            const el = document.querySelector(sel);
            if (el) return el;
        }

        // Fallback: find the text input nearest to the captcha image
        const captchaImg = getCaptchaImage();
        if (captchaImg) {
            const parent = captchaImg.closest(".row, .form-group, div");
            if (parent) {
                const input = parent.querySelector('input[type="text"]');
                if (input) return input;
            }
            // Try sibling or next row
            const nextRow = captchaImg.closest(".row, div")?.nextElementSibling;
            if (nextRow) {
                const input = nextRow.querySelector('input[type="text"]');
                if (input) return input;
            }
        }

        return null;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    //  SOLVE CAPTCHA
    // ═══════════════════════════════════════════════════════════════════════════

    async function solveCaptcha() {
        if (isSolving) return;
        isSolving = true;

        setStatus("Finding captcha image...", "yellow");

        const captchaImg = getCaptchaImage();
        if (!captchaImg) {
            setStatus("❌ Captcha image not found!", "red");
            isSolving = false;
            return;
        }

        // Wait for image to load
        if (!captchaImg.complete) {
            await new Promise((resolve) => {
                captchaImg.onload = resolve;
                captchaImg.onerror = resolve;
            });
        }

        setStatus("Extracting image...", "yellow");

        let base64;
        try {
            base64 = await imageToBase64(captchaImg);
        } catch (e) {
            // If canvas fails (CORS), try fetching directly
            try {
                base64 = await fetchImageAsBase64(captchaImg.src);
            } catch (e2) {
                setStatus("❌ Failed to extract image", "red");
                isSolving = false;
                return;
            }
        }

        setStatus("Sending to OCR server...", "yellow");

        GM_xmlhttpRequest({
            method: "POST",
            url: CONFIG.SERVER_URL,
            headers: { "Content-Type": "application/json" },
            data: JSON.stringify({ image: base64 }),
            onload: (response) => {
                try {
                    const data = JSON.parse(response.responseText);

                    if (data.error) {
                        setStatus(`❌ Server error: ${data.error}`, "red");
                        isSolving = false;
                        return;
                    }

                    const text = data.text || "";
                    const confidence = data.confidence || 0;
                    const allResults = data.all_results || [];

                    if (!text) {
                        setStatus("❌ No text detected", "red");
                        handleRetry();
                        return;
                    }

                    if (confidence < CONFIG.MIN_CONFIDENCE) {
                        setStatus(`⚠ Low confidence (${confidence}%)`, "yellow");
                        setResult(text, confidence, allResults);
                        handleRetry();
                        return;
                    }

                    // Success!
                    setStatus("✅ Solved!", "green");
                    setResult(text, confidence, allResults);

                    if (CONFIG.AUTO_FILL) {
                        fillCaptchaInput(text);
                    }

                    isSolving = false;
                    retryCount = 0;
                } catch (e) {
                    setStatus(`❌ Parse error: ${e.message}`, "red");
                    isSolving = false;
                }
            },
            onerror: (err) => {
                setStatus("❌ Server offline! Start server.py first", "red");
                isSolving = false;
            },
        });
    }

    function fillCaptchaInput(text) {
        const input = getCaptchaInput();
        if (input) {
            // Set value and trigger events so Angular/React/jQuery detects the change
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype,
                "value"
            ).set;
            nativeInputValueSetter.call(input, text);

            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.dispatchEvent(new Event("change", { bubbles: true }));
            input.dispatchEvent(new Event("keyup", { bubbles: true }));

            setStatus(`✅ Filled: "${text}"`, "green");
        } else {
            setStatus(`✅ Solved: "${text}" (input field not found — paste manually)`, "green");
        }
    }

    function handleRetry() {
        if (!CONFIG.AUTO_RETRY_ON_FAIL || retryCount >= CONFIG.MAX_RETRIES) {
            isSolving = false;
            return;
        }

        retryCount++;
        setStatus(`Retrying (${retryCount}/${CONFIG.MAX_RETRIES})...`, "yellow");

        setTimeout(() => {
            isSolving = false;
            refreshCaptcha();
        }, CONFIG.RETRY_DELAY_MS);
    }

    // ═══════════════════════════════════════════════════════════════════════════
    //  REFRESH CAPTCHA
    // ═══════════════════════════════════════════════════════════════════════════

    function refreshCaptcha() {
        const captchaImg = getCaptchaImage();
        if (!captchaImg) {
            setStatus("❌ Captcha image not found", "red");
            return;
        }

        // Append timestamp to force reload (bypass cache)
        const baseUrl = captchaImg.src.split("?")[0];
        captchaImg.src = `${baseUrl}?rand=${Date.now()}`;

        setStatus("Loading new captcha...", "yellow");
        setResult("", 0);

        captchaImg.onload = () => {
            if (CONFIG.AUTO_SOLVE) {
                setTimeout(solveCaptcha, 300);
            } else {
                setStatus("New captcha loaded. Click Solve.", "yellow");
            }
        };
    }

    // ═══════════════════════════════════════════════════════════════════════════
    //  HEALTH CHECK & INIT
    // ═══════════════════════════════════════════════════════════════════════════

    function checkServer() {
        GM_xmlhttpRequest({
            method: "GET",
            url: CONFIG.HEALTH_URL,
            onload: (response) => {
                try {
                    const data = JSON.parse(response.responseText);
                    if (data.status === "ok") {
                        setStatus(`Server online (Tesseract ${data.tesseract_version})`, "green");
                        if (CONFIG.AUTO_SOLVE) {
                            setTimeout(solveCaptcha, 500);
                        }
                    } else {
                        setStatus(`⚠ ${data.message}`, "red");
                    }
                } catch (e) {
                    setStatus("⚠ Invalid server response", "red");
                }
            },
            onerror: () => {
                setStatus("❌ Server offline — run: python server.py", "red");
            },
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    //  BOOT
    // ═══════════════════════════════════════════════════════════════════════════

    // Wait for page to settle, then init
    setTimeout(() => {
        createPanel();
        checkServer();
    }, 1000);

    // Also watch for dynamically loaded captcha images (SPA navigation)
    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {
                if (node.nodeName === "IMG" && node.src && node.src.includes("captcha")) {
                    node.onload = () => {
                        if (CONFIG.AUTO_SOLVE && !isSolving) {
                            setTimeout(solveCaptcha, 300);
                        }
                    };
                }
            }
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
})();
