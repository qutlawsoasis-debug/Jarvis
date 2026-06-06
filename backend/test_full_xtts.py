"""Финальный тест: синтез через XTTS API + воспроизведение через winsound"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

# Добавляем backend в путь
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv('.env')

import os
os.environ['TTS_ENGINE'] = 'local_xtts'

# Импортируем функции из основного модуля
import requests
import winsound

def generate_voice_local_xtts(text, filename="response.wav"):
    url = "http://localhost:5002/tts_to_audio/"
    speakers_dir = os.path.join(os.path.dirname(__file__), "speakers")
    speaker_file = os.getenv("XTTS_SPEAKER", "patrick.wav").strip()
    
    if not os.path.exists(os.path.join(speakers_dir, speaker_file)):
        if os.path.exists(speakers_dir):
            wav_files = [f for f in os.listdir(speakers_dir) if f.endswith('.wav')]
            if wav_files:
                speaker_file = wav_files[0]
            else:
                speaker_file = "speaker.wav"
        else:
            speaker_file = "speaker.wav"
    
    print(f"[XTTS] Спикер: {speaker_file}")
    payload = {"text": text, "language": "ru", "speaker_wav": speaker_file}
    
    r = requests.post(url, json=payload, timeout=60)
    if r.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(r.content)
        print(f"[XTTS] Аудио создано: {os.path.getsize(filename)} байт")
        return True
    else:
        print(f"[XTTS] Ошибка {r.status_code}: {r.text}")
        return False

def play_wav(filename):
    abs_path = os.path.abspath(filename)
    winsound.PlaySound(abs_path, winsound.SND_FILENAME)

test_phrases = [
    "Системы инициализированы. Я на связи, сэр.",
    "Добрый день, Мирон. Чем могу помочь?",
]

for phrase in test_phrases:
    print(f"\nТекст: {phrase}")
    import time
    t0 = time.time()
    ok = generate_voice_local_xtts(phrase, "test_final.wav")
    print(f"Генерация: {time.time()-t0:.2f}с")
    if ok:
        print("Воспроизвожу...")
        play_wav("test_final.wav")
        print("Готово!")
    else:
        print("Ошибка генерации!")

print("\n=== Тест завершён ===")
