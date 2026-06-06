import os
import sys
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

api_key = "62af6c8117d191cd05e14e866cfa18c7820cc2b45746d4d153f1e096921667b7"

deep_voices = [
    ("Charlie (Deep, Confident, Energetic)", "IKne3meq5aSn9XLyUdCD"),
    ("Brian (Deep, Resonant and Comforting)", "nPczCjzI2devNBz1zQrb"),
    ("Adam (Dominant, Firm)", "pNInz6obpgDQGcFmaJgB")
]

url_template = "https://api.elevenlabs.io/v1/text-to-speech/{}"
headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": api_key
}

for name, voice_id in deep_voices:
    print(f"\n🎙️ Тестирую голос: {name} [ID: {voice_id}]")
    text = f"Привет! Я твой новый голосовой ассистент, и это демонстрация моего глубокого голоса под именем {name.split()[0]}. Как тебе такой тембр?"
    
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.55,
            "similarity_boost": 0.75
        }
    }
    
    try:
        response = requests.post(url_template.format(voice_id), json=payload, headers=headers, timeout=20)
        if response.status_code == 200:
            filename = f"test_{voice_id}.mp3"
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"   [УСПЕХ] Файл сгенерирован: {filename}")
            
            # Воспроизведение через PowerShell
            import subprocess
            import time
            abs_path = os.path.abspath(filename)
            print("   Воспроизвожу...")
            subprocess.run(
               ['powershell', '-Command',
                f'$p = New-Object System.Windows.Media.MediaPlayer; $p.Open([uri]"{abs_path}"); $p.Play(); Start-Sleep -Seconds 6; $p.Stop()'],
               timeout=10, capture_output=True
            )
        else:
            print(f"   [Ошибка ElevenLabs {response.status_code}]: {response.text}")
    except Exception as e:
        print(f"   [Ошибка]: {e}")
