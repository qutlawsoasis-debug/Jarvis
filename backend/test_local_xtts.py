import os
import requests
import ctypes

def play_audio(filename="response.wav"):
    try:
        abs_path = os.path.abspath(filename)
        # Открываем, проигрываем и закрываем файл через MCI
        ctypes.windll.winmm.mciSendStringW(f'open "{abs_path}" alias my_sound', None, 0, 0)
        ctypes.windll.winmm.mciSendStringW('play my_sound wait', None, 0, 0)
        ctypes.windll.winmm.mciSendStringW('close my_sound', None, 0, 0)
    except Exception as e:
        print(f"[Ошибка воспроизведения]: {e}")

def test_xtts():
    url = "http://localhost:5002/api/tts"
    
    # Ищем файлы клонирования голоса в папке speakers
    speaker_file = "speaker.wav"
    speakers_dir = os.path.join(os.path.dirname(__file__), "speakers")
    if os.path.exists(speakers_dir):
        files = [f for f in os.listdir(speakers_dir) if f.endswith(('.wav', '.mp3'))]
        if files:
            speaker_file = files[0]
    
    print(f"Используемый файл спикера: {speaker_file}")
    
    payload = {
        "text": "Привет! Это проверка работы локального синтеза речи Coqui XTTS v2. Системы работают в штатном режиме.",
        "language": "ru",
        "speaker_wav": speaker_file,
    }
    
    try:
        print("Отправка запроса на генерацию речи...")
        response = requests.post(url, json=payload, timeout=40)
        if response.status_code == 200:
            filename = "test_response.wav"
            if os.path.exists(filename):
                os.remove(filename)
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"[УСПЕХ] Файл {filename} успешно сгенерирован! Воспроизведение...")
            play_audio(filename)
        else:
            print(f"[Ошибка API {response.status_code}]: {response.text}")
    except Exception as e:
        print(f"[Ошибка соединения]: {e}")

if __name__ == "__main__":
    test_xtts()
