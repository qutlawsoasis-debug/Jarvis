import requests

api_key = "62af6c8117d191cd05e14e866cfa18c7820cc2b45746d4d153f1e096921667b7"
url = "https://api.elevenlabs.io/v1/voices"
headers = {"xi-api-key": api_key}

try:
    print("Запрос списка доступных голосов в ElevenLabs...")
    r = requests.get(url, headers=headers)
    print("Статус:", r.status_code)
    if r.status_code == 200:
        voices_data = r.json()
        voices = voices_data.get("voices", [])
        print(f"Найдено голосов: {len(voices)}")
        
        # Выведем первые 20 голосов
        for idx, v in enumerate(voices):
            category = v.get("category", "unknown")
            print(f"[{idx}] Имя: {v.get('name')}, ID: {v.get('voice_id')}, Категория: {category}")
    else:
        print("Ошибка:", r.text)
except Exception as e:
    print("Ошибка соединения:", e)
