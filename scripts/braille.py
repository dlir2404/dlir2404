"""Braille ASCII art: each character encodes a 2x4 block of dithered dots."""
import sys
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageEnhance

src, cols, mode = sys.argv[1], int(sys.argv[2]), sys.argv[3]
contrast = float(sys.argv[4]) if len(sys.argv) > 4 else 1.4
DOT_ASPECT = 0.96                      # dot width / height for 9.6x20px cells

rgba = Image.open(src).convert("RGBA")
rgba = rgba.crop(rgba.getchannel("A").point(lambda a: 255 if a > 20 else 0).getbbox())
w, h = rgba.size
pw = cols * 2
ph = int(round(pw * (h / w) * DOT_ASPECT / 4)) * 4
img = rgba.resize((pw, ph), Image.LANCZOS)
alpha = np.asarray(img.getchannel("A"), dtype=np.float32) / 255
gray = ImageOps.autocontrast(img.convert("L"), cutoff=1)
gray = gray.filter(ImageFilter.UnsharpMask(radius=2, percent=160, threshold=2))
gray = ImageEnhance.Contrast(gray).enhance(contrast)
lum = np.asarray(gray, dtype=np.float32) / 255
if mode == "light":
    lum = 1 - lum
lum = lum * (alpha > 0.5)
dots = np.asarray(Image.fromarray((lum * 255).astype(np.uint8)).convert("1"), dtype=bool)

BITS = [(0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04), (1, 0, 0x08), (1, 1, 0x10), (1, 2, 0x20), (0, 3, 0x40), (1, 3, 0x80)]
lines = []
for r in range(ph // 4):
    line = ""
    for c in range(cols):
        code = 0
        for dx, dy, bit in BITS:
            if dots[r * 4 + dy, c * 2 + dx]:
                code |= bit
        line += chr(0x2800 + code)
    lines.append(line)
print("\n".join(lines))
