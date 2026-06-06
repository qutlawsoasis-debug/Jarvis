import os
import requests
from dotenv import load_dotenv

# Загружаем настройки из .env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")

print("API KEY:", ELEVENLABS_API_KEY)
print("VOICE ID:", ELEVENLABS_VOICE_ID)

text = "Привет! Я Роджер, твой новый голосовой ассистент. Системы работают штатно, качество звука превосходное."
url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": ELEVENLABS_API_KEY
}
payload = {
    "text": text,
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
        "stability": 0.55,
        "similarity_boost": 0.75
    }
}

try:
    print("Отправка запроса в ElevenLabs...")
    response = requests.post(url, json=payload, headers=headers, timeout=20)
    print("Статус-код:", response.status_code)
    if response.status_code == 200:
        filename = "test_new_elevenlabs.mp3"
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"[УСПЕХ] Файл сгенерирован: {filename} ({os.path.getsize(filename)} байт)")
        
        # Воспроизведение через PowerShell
        import subprocess
        abs_path = os.path.abspath(filename)
        print("Воспроизвожу...")
        subprocess.run(
            ['powershell', '-Command',
             f'$p = New-Object System.Windows.Media.MediaPlayer; $p.Open([uri]"{abs_path}"); $p.Play(); Start-Sleep -Seconds 6; $p.Stop()'],
            timeout=10, capture_output=True
        )
    else:
        print(f"[Ошибка ElevenLabs {response.status_code}]: {response.text}")
except Exception as e:
    print(f"[Ошибка]: {e}")
