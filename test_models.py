import base64, io, json, urllib.request
from PIL import Image, ImageDraw, ImageFont
import config

img = Image.new("RGB", (200, 50), "white")
d = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype("arial.ttf", 32)
except Exception:
    font = ImageFont.load_default()
d.text((20, 8), "A7B3K", fill="black", font=font)
d.line((0, 25, 200, 25), fill="gray", width=2)
buf = io.BytesIO(); img.save(buf, format="PNG")
b64 = base64.b64encode(buf.getvalue()).decode()

for model in [
    "nvidia/nemotron-3.5-super-vl:free",
    "google/gemma-4-26b-a4b-it:free",
    "dots-studio/dots-3-note-preview:free",
    "thinkingmachines/inkling:free",
]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "Solve the captcha. Reply with ONLY the characters, nothing else."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ]}],
        "temperature": 0.0, "max_tokens": 600,
    }
    req = urllib.request.Request(
        config.OPENROUTER_URL,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            res = json.loads(r.read().decode())
        ch = res.get("choices", [{}])[0]
        msg = ch.get("message", {})
        usage = res.get("usage", {})
        print(f"{model}")
        print(f"  finish={ch.get('finish_reason')} content={msg.get('content')!r}")
        print(f"  img_tokens={(usage.get('prompt_tokens_details') or {}).get('image_tokens')} "
              f"prompt_tokens={usage.get('prompt_tokens')}")
    except urllib.error.HTTPError as e:
        print(f"{model} -> HTTP {e.code}: {e.read().decode()[:200]}")
    except Exception as e:
        print(f"{model} -> {type(e).__name__}: {e}")
