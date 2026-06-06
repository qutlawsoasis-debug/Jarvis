import os
import requests
import winsound
import time

url = "http://localhost:5002/tts_to_audio/"
speaker_file = "egor.wav"
text = "Привет, Мирон! Я твой новый голосовой ассистент Джарвис, заговорю голосом Егора Гаджиева. Системы инициализированы."

print(f"[XTTS] Спикер: {speaker_file}")
payload = {"text": text, "language": "ru", "speaker_wav": speaker_file}

t0 = time.time()
r = requests.post(url, json=payload, timeout=60)
print(f"Генерация заняла: {time.time()-t0:.2f}с")

if r.status_code == 200:
    filename = "test_egor.wav"
    with open(filename, 'wb') as f:
        f.write(r.content)
    print(f"[XTTS] Аудио создано: {os.path.getsize(filename)} байт. Воспроизвожу...")
    winsound.PlaySound(os.path.abspath(filename), winsound.SND_FILENAME)
    print("Успешно!")
else:
    print(f"[XTTS] Ошибка {r.status_code}: {r.text}")
