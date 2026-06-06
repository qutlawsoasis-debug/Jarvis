import requests
import json
import os
import subprocess

api_key = "62af6c8117d191cd05e14e866cfa18c7820cc2b45746d4d153f1e096921667b7"
target_voice_id = "6A9D8WSMm4rFsg2DWFeE"

url = "https://api.elevenlabs.io/v1/shared-voices"
params = {
    "search": "Egor Gadzhiyev",
    "page_size": 10
}
headers = {"xi-api-key": api_key}

try:
    print("Ищу голос Egor Gadzhiyev в библиотеке ElevenLabs...")
    r = requests.get(url, params=params, headers=headers)
    print("Статус:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        voices = data.get("voices", [])
        print(f"Найдено совпадений: {len(voices)}")
        
        found_voice = None
        for v in voices:
            print(f"Найдено: Name='{v.get('name')}', ID='{v.get('voice_id')}'")
            if v.get("voice_id") == target_voice_id:
                found_voice = v
                break
                
        # Если не нашли по точному поиску имени, запросим общую страницу или попробуем найти среди всех
        if not found_voice and voices:
            found_voice = voices[0] # возьмем первый
            
        if found_voice:
            preview_url = found_voice.get("preview_url")
            print("Ссылка на превью:", preview_url)
            
            if preview_url:
                # Скачиваем MP3
                mp3_path = "backend/speakers/tmp/egor_preview.mp3"
                os.makedirs(os.path.dirname(mp3_path), exist_ok=True)
                print(f"Скачиваю MP3 превью в {mp3_path}...")
                audio_r = requests.get(preview_url)
                if audio_r.status_code == 200:
                    with open(mp3_path, "wb") as f:
                        f.write(audio_r.content)
                    print("Скачивание завершено!")
                    
                    # Конвертируем в WAV через ffmpeg
                    ffmpeg_path = os.path.abspath("backend/.venv/Scripts/ffmpeg.exe")
                    wav_path = "backend/speakers/egor.wav"
                    print(f"Конвертирую в WAV: {wav_path} ...")
                    cmd = [ffmpeg_path, "-i", mp3_path, "-ar", "22050", "-ac", "1", "-y", wav_path]
                    sub_r = subprocess.run(cmd, capture_output=True)
                    if sub_r.returncode == 0:
                        print(f"[УСПЕХ] Голос Egor Gadzhiyev сохранен как {wav_path}!")
                        # Чистим временный файл
                        os.remove(mp3_path)
                    else:
                        print("Ошибка конвертации ffmpeg:", sub_r.stderr.decode('utf-8', errors='ignore'))
                else:
                    print("Не удалось скачать аудио:", audio_r.text)
            else:
                print("У этого голоса нет preview_url!")
        else:
            print(f"Голос с ID {target_voice_id} не найден в результатах поиска.")
            # Если не нашли поиском по имени, попробуем загрузить напрямую с помощью shared-voices без фильтра
            # или попробуем найти его через обычный get-shared-voices постранично.
    else:
        print("Ошибка запроса:", r.text)
except Exception as e:
    print("Ошибка:", e)
