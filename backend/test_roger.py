import os
import requests
from dotenv import load_dotenv

api_key = "62af6c8117d191cd05e14e866cfa18c7820cc2b45746d4d153f1e096921667b7"
voice_id = "CwhRBWXzGAHq8TQ4Fs17" # Roger (premade)

text = "Привет! Я Роджер, твой новый голосовой ассистент. Системы работают штатно, качество звука превосходное."
url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": api_key
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
    print("Отправка запроса в ElevenLabs (Роджер)...")
    response = requests.post(url, json=payload, headers=headers, timeout=20)
    print("Статус-код:", response.status_code)
    if response.status_code == 200:
        filename = "test_roger.mp3"
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
