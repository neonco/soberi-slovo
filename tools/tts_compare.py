#!/usr/bin/env python3
"""Генерация тестовых слогов/слов/фраз разными локальными TTS в одну папку.
Только генерация, без оценки. Запуск на Mac (Apple Silicon):

  python3 -m venv .venv-tts && source .venv-tts/bin/activate
  pip install soundfile numpy torch torchaudio            # Silero
  pip install mlx-audio                                   # Qwen3-TTS
  pip install f5-tts ruaccent huggingface_hub             # ESpeech
  python tools/tts_compare.py --engines silero            # по одной модели
  python tools/tts_compare.py --engines silero,qwen3,espeech \\
      --ref-audio ref.wav --ref-text "текст образца"      # ref нужен для espeech

Результат: out/tts_compare/<engine>/<id>__<темп>.wav
Не проверено на реальном железе: если API модели изменился, правьте нужную функцию.
"""
import argparse
import sys
from pathlib import Path

# (id, текст). Слоги для TTS пишем как короткое слово: одиночная буква-слог читается плохо.
SYLLABLES = ["ма", "па", "ба", "ку", "ня", "ся", "ша", "жу", "ры", "ль", "до", "ти", "ке", "ля", "ву"]
WORDS = ["мама", "папа", "мороженое", "молоко", "собака", "кот", "дом", "банан", "машина", "вода"]
PHRASES = ["покажи", "молодец", "попробуй ещё", "это мама", "правильно"]
ITEMS = [("s_" + t, t) for t in SYLLABLES] + [("w_" + t, t) for t in WORDS] + [("p_" + t.replace(" ", "_"), t) for t in PHRASES]

# нормальный и медленный темп; у каждой модели свой механизм (см. функции ниже)
TEMPOS = {"normal": 1.0, "slow": 0.6}


def save(path, audio, sr):
    import numpy as np
    import soundfile as sf
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), np.asarray(audio, dtype="float32").squeeze(), sr)


def run_silero(out, repeats, speaker):
    import torch
    model, _ = torch.hub.load("snakers4/silero-models", "silero_tts", language="ru", speaker="v5_ru", trust_repo=True)
    rate = {"normal": "medium", "slow": "x-slow"}  # SSML prosody rate
    sr = 48000
    for id_, text in ITEMS:
        for tempo in TEMPOS:
            ssml = f'<speak><prosody rate="{rate[tempo]}">{text}</prosody></speak>'
            for i in range(repeats):
                audio = model.apply_tts(ssml_text=ssml, speaker=speaker, sample_rate=sr)
                save(out / "silero" / f"{id_}__{tempo}_{i+1}.wav", audio.numpy(), sr)
        print("silero", id_)


def run_qwen3(out, repeats, model_id, voice):
    from mlx_audio.tts.utils import load_model
    model = load_model(model_id)
    for id_, text in ITEMS:
        for tempo in TEMPOS:
            # у Qwen3 темп задаётся только текстом/инструкцией, нативного speed нет:
            # для slow даём паузы между буквами слога, это грубо, смотрите на результат
            gen_text = text if tempo == "normal" else "... " + text
            for i in range(repeats):
                chunks, sr = [], 24000
                for r in model.generate(gen_text, voice=voice, lang_code="Russian"):
                    chunks.append(r.audio)
                    sr = getattr(model, "sample_rate", sr)
                import numpy as np
                audio = np.concatenate([np.array(c).reshape(-1) for c in chunks])
                save(out / "qwen3" / f"{id_}__{tempo}_{i+1}.wav", audio, sr)
        print("qwen3", id_)


def run_espeech(out, repeats, ref_audio, ref_text):
    if not (ref_audio and ref_text):
        print("espeech: пропуск, нужны --ref-audio и --ref-text (запись голоса до 12 с)", file=sys.stderr)
        return
    from huggingface_hub import hf_hub_download
    from f5_tts.infer.utils_infer import infer_process, load_model, load_vocoder, preprocess_ref_audio_text
    from f5_tts.model import DiT
    from ruaccent import RUAccent

    repo = "ESpeech/ESpeech-TTS-1_SFT-256K"
    ckpt = hf_hub_download(repo, "espeech_tts_256k.pt")
    vocab = hf_hub_download(repo, "vocab.txt")
    cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)
    model = load_model(DiT, cfg, ckpt, vocab_file=vocab)
    vocoder = load_vocoder()
    acc = RUAccent()
    acc.load(omograph_model_size="turbo3.1", use_dictionary=True, tiny_mode=False)
    ref_audio_p, ref_text_p = preprocess_ref_audio_text(ref_audio, acc.process_all(ref_text))
    for id_, text in ITEMS:
        gen = acc.process_all(text)
        for tempo, speed in TEMPOS.items():
            for i in range(repeats):
                wave, sr, _ = infer_process(ref_audio_p, ref_text_p, gen, model, vocoder,
                                            cross_fade_duration=0.15, nfe_step=32, speed=speed)
                save(out / "espeech" / f"{id_}__{tempo}_{i+1}.wav", wave, sr)
        print("espeech", id_)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--engines", default="silero", help="silero,qwen3,espeech")
    p.add_argument("--out", default="out/tts_compare")
    p.add_argument("--repeats", type=int, default=3, help="сколько раз генерировать каждую единицу (для проверки стабильности)")
    p.add_argument("--silero-speaker", default="xenia")
    p.add_argument("--qwen3-model", default="mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit")
    p.add_argument("--qwen3-voice", default="Chelsie")
    p.add_argument("--ref-audio")
    p.add_argument("--ref-text")
    a = p.parse_args()
    out = Path(a.out)
    for e in a.engines.split(","):
        e = e.strip()
        if e == "silero":
            run_silero(out, a.repeats, a.silero_speaker)
        elif e == "qwen3":
            run_qwen3(out, a.repeats, a.qwen3_model, a.qwen3_voice)
        elif e == "espeech":
            run_espeech(out, a.repeats, a.ref_audio, a.ref_text)
        else:
            sys.exit(f"неизвестный движок: {e}")


if __name__ == "__main__":
    main()
