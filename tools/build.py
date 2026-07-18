#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Сборка prototype/index.html из шаблона + данных.
ЗАПУСКАТЬ после любой правки index.template.html или JSON-баз:
    python tools/build.py
"""
from pathlib import Path
import json, re, sys

ROOT = Path(__file__).resolve().parent.parent
tpl = (ROOT / 'prototype' / 'index.template.html').read_text(encoding='utf-8')
data_raw = (ROOT / 'content' / 'syllable-cards.json').read_text(encoding='utf-8').strip()
extra_raw = (ROOT / 'content' / 'extra-cards.json').read_text(encoding='utf-8').strip()
out = tpl.replace('/*__DATA__*/', data_raw)
out = out.replace('/*__EXTRA__*/', extra_raw)
assert '/*__DATA__*/' not in out and '/*__EXTRA__*/' not in out, 'плейсхолдеры не заменены'

# валидация JSON-данных перед сборкой
try:
    data = json.loads(data_raw)
    extra = json.loads(extra_raw)
except json.JSONDecodeError as e:
    print('ОШИБКА: невалидный JSON:', e); sys.exit(1)

errors = []
for level in data.get('levels', []):
    for w in level.get('words', []):
        word = w.get('word', '')
        syls = w.get('syllables', [])
        stress = w.get('stress', 0)
        image = w.get('image', '')
        if ''.join(syls) != word:
            errors.append(f"{word} (уровень {level.get('id')}): слоги {'-'.join(syls)} не склеиваются в слово")
        if not (0 <= stress < len(syls)):
            errors.append(f"{word} (уровень {level.get('id')}): stress={stress} вне диапазона 0..{len(syls)-1}")
        if not image:
            errors.append(f"{word} (уровень {level.get('id')}): отсутствует image")

if errors:
    print('ОШИБКИ В ДАННЫХ:')
    for e in errors:
        print(' -', e)
    sys.exit(1)
(ROOT / 'prototype' / 'index.html').write_text(out, encoding='utf-8')

# проверка: все id, используемые в JS, существуют в HTML
js = re.search(r'<script>(.*)</script>', out, re.S).group(1)
ids_in_html = set(re.findall(r'id="(\w+)"', out))
ids_used = set(re.findall(r"\$\('(\w+)'\)", js))
missing = ids_used - ids_in_html
if missing:
    print('ОШИБКА: нет элементов с id:', missing); sys.exit(1)
print(f'OK: index.html собран ({len(out)} байт), id в порядке')
