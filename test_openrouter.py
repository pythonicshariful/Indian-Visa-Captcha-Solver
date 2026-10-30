import base64, io, json, urllib.request
from PIL import Image, ImageDraw, ImageFont

# Build a synthetic captcha-like image with known text
img = Image.new("RGB", (200, 50), "white")
d = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype("arial.ttf", 32)
except Exception:
    font = ImageFont.load_default()
d.text((20, 8), "A7B3K", fill="black", font=font)
# draw a distractor line
d.line((0, 25, 200, 25), fill="gray", width=2)

buf = io.BytesIO()
img.save(buf, format="PNG")
b64 = base64.b64encode(buf.getvalue()).decode()

data = json.dumps({"image": b64}).encode()
req = urllib.request.Request("http://127.0.0.1:5555/solve", data=data,
                             headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=60) as r:
    print("RESPONSE:", r.read().decode())
