import os
import requests
import winsound
import time

api_key = "1be2a23c03eb485eb31a77903ebfa078"
voice_id = "2084dc1e0e85483c840eb7484c64fc8c"

url = "https://api.fish.audio/v1/tts"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
    "text": "Привет, Мирон! Я твой новый голосовой ассистент Джарвис, заговорю голосом Егора Гаджиева через Fish Audio. Системы работают превосходно.",
    "reference_id": voice_id
}

print(f"Отправка запроса в Fish Audio с ID модели: {voice_id} ...")
t0 = time.time()
r = requests.post(url, headers=headers, json=payload)
print("Статус-код:", r.status_code)
print(f"Запрос занял: {time.time()-t0:.2f}с")

if r.status_code == 200:
    filename = "test_fish.mp3"
    with open(filename, 'wb') as f:
        f.write(r.content)
    print(f"[УСПЕХ] Файл сгенерирован: {filename} ({os.path.getsize(filename)} байт). Воспроизвожу...")
    
    # Воспроизведение через PowerShell
    import subprocess
    abs_path = os.path.abspath(filename)
    subprocess.run(
       ['powershell', '-Command',
        f'$p = New-Object System.Windows.Media.MediaPlayer; $p.Open([uri]"{abs_path}"); $p.Play(); Start-Sleep -Seconds 6; $p.Stop()'],
       timeout=10, capture_output=True
    )
    print("Готово!")
else:
    print("Ошибка API:", r.text)
