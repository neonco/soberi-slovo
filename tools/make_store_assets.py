#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Генерация ассетов для магазинов (Rustore / Google Play):
  - store/icon-512.png         (иконка приложения 512x512)
  - store/feature-graphic.png  (1024x500, градиент + текст)
ЗАПУСК: python tools/make_store_assets.py
"""
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'store'
OUT.mkdir(exist_ok=True)


def font(size, bold=True):
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    for c in candidates:
        p = Path(c)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                pass
    return ImageFont.load_default()


def vgradient(w, h, top, bottom):
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        d.line([(0, y), (w, y)], fill=(r, g, b, 255))
    return img


def centered(d, text, box, fnt, fill):
    bbox = d.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = box[0] + (box[2] - box[0] - tw) / 2 - bbox[0]
    y = box[1] + (box[3] - box[1] - th) / 2 - bbox[1]
    d.text((x, y), text, font=fnt, fill=fill)


def make_icon():
    s = 512
    img = vgradient(s, s, (244, 237, 225), (107, 143, 113))
    d = ImageDraw.Draw(img)
    fnt = font(int(s * 0.22))
    centered(d, "СЛОВО", (0, 0, s, s), fnt, (255, 255, 255, 255))
    img.save(OUT / "icon-512.png")
    print("OK icon-512.png")


def make_feature():
    w, h = 1024, 500
    img = vgradient(w, h, (107, 143, 113), (244, 237, 225))
    d = ImageDraw.Draw(img)
    centered(d, "Собери слово", (0, 40, w, 240), font(110), (255, 255, 255, 255))
    centered(d, "логопедия для детей 5+", (0, 250, w, 380), font(54), (60, 80, 65, 255))
    img.save(OUT / "feature-graphic.png")
    print("OK feature-graphic.png")


if __name__ == "__main__":
    make_icon()
    make_feature()
