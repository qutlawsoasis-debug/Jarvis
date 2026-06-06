import requests
import os
import sys
import json

api_key = "1be2a23c03eb485eb31a77903ebfa078"
url = "https://api.fish.audio/model"
headers = {"Authorization": f"Bearer {api_key}"}

# Проверяем наличие файла egor.wav
wav_path = "backend/speakers/egor.wav"
if not os.path.exists(wav_path):
    print(f"Ошибка: Файл {wav_path} не найден!")
    sys.exit(1)

print(f"Загружаю {wav_path} в Fish Audio для создания модели голоса...")

files = {
    "voices": ("egor.wav", open(wav_path, "rb"), "audio/wav")
}
data = {
    "type": "tts",
    "train_mode": "fast",
    "title": "Egor Jarvis",
    "visibility": "private"
}

try:
    r = requests.post(url, headers=headers, files=files, data=data)
    print("Статус-код:", r.status_code)
    if r.status_code in [200, 201]:
        res_data = r.json()
        print("Ответ сервера:")
        print(json.dumps(res_data, indent=2, ensure_ascii=False))
        # Извлекаем ID модели
        model_id = res_data.get("id")
        print(f"\n[УСПЕХ] Модель успешно создана! ID модели: {model_id}")
    else:
        print("Ошибка создания модели:", r.text)
except Exception as e:
    print("Ошибка соединения:", e)
