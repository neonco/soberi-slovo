#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Генерация иконок приложения (mipmap) для Android из простого градиента + текста.
ЗАПУСК: python tools/make_icons.py
Результат: android/app/src/main/res/mipmap-*/ic_launcher.png (+ round)
"""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SIZES = {
    'mipmap-mdpi': 48,
    'mipmap-hdpi': 72,
    'mipmap-xhdpi': 96,
    'mipmap-xxhdpi': 144,
    'mipmap-xxxhdpi': 192,
}


def font_for(size):
    # Пытаемся найти системный шрифт с кириллицей; fallback — дефолт
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/seguiemj.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for c in candidates:
        p = Path(c)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), max(10, int(size * 0.30)))
            except Exception:
                pass
    return ImageFont.load_default()


def make_icon(size, round_corner=False):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # фон — тёплый градиент (hero-цвет из приложения #f4ede1 -> #6b8f71)
    for y in range(size):
        t = y / size
        r = int(244 + (107 - 244) * t)
        g = int(237 + (143 - 237) * t)
        b = int(225 + (113 - 225) * t)
        d.line([(0, y), (size, y)], fill=(r, g, b, 255))
    if round_corner:
        # вырезаем скруглённые углы (радиус ~20%)
        rad = int(size * 0.22)
        mask = Image.new("L", (size, size), 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle([0, 0, size, size], radius=rad, fill=255)
        img.putalpha(mask)
    # текст «СЛОВО»
    fnt = font_for(size)
    text = "СЛОВО"
    try:
        bbox = d.textbbox((0, 0), text, font=fnt)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        tw, th = size * 0.8, size * 0.3
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1]
    d.text((x, y), text, font=fnt, fill=(255, 255, 255, 255))
    return img


def main():
    for folder, size in SIZES.items():
        out_dir = ROOT / "android" / "app" / "src" / "main" / "res" / folder
        out_dir.mkdir(parents=True, exist_ok=True)
        make_icon(size, round_corner=False).save(out_dir / "ic_launcher.png")
        make_icon(size, round_corner=True).save(out_dir / "ic_launcher_round.png")
        print(f"OK {folder}: {size}px")


if __name__ == "__main__":
    main()
