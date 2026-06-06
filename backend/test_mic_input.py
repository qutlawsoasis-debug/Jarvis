import speech_recognition as sr
import time

for idx in [1, 2]:
    print(f"\n--- Тестирую микрофон с индексом {idx} ---")
    try:
        m = sr.Microphone(device_index=idx)
        r = sr.Recognizer()
        r.energy_threshold = 300
        
        print("Говорите что-нибудь в микрофон в течение 3 секунд...")
        with m as source:
            # Калибровка под шум
            r.adjust_for_ambient_noise(source, duration=0.5)
            print(f"Калибровка завершена. Установлен порог громкости: {r.energy_threshold}")
            
            try:
                # Слушаем короткую фразу
                audio = r.listen(source, timeout=3, phrase_time_limit=3)
                print("Звук получен! Попытка распознавания...")
                text = r.recognize_google(audio, language="ru-RU")
                print(f"Распознано: '{text}'")
            except sr.WaitTimeoutError:
                print("Таймаут: звук не обнаружен.")
            except sr.UnknownValueError:
                print("Звук услышан, но не распознан как речь.")
            except Exception as e:
                print(f"Ошибка при прослушивании: {e}")
    except Exception as e:
        print(f"Ошибка инициализации микрофона {idx}: {e}")
