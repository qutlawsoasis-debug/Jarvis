import speech_recognition as sr
import pyaudio

def test_audio():
    print("==================================================")
    print("        ТЕСТИРОВАНИЕ АУДИОУСТРОЙСТВ               ")
    print("==================================================")
    
    # 1. Проверка PyAudio устройств
    try:
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        print(f"Всего обнаружено аудиоустройств: {numdevices}\n")
        
        inputs = 0
        for i in range(0, numdevices):
            device_info = p.get_device_info_by_host_api_device_index(0, i)
            if device_info.get('maxInputChannels') > 0:
                print(f"Входное устройство [{i}]: {device_info.get('name')}")
                inputs += 1
                
        if inputs == 0:
            print("[ВНИМАНИЕ]: Не обнаружено ни одного микрофона (входного устройства)!")
            
    except Exception as e:
        print(f"[ОШИБКА PyAudio]: {e}")
        return

    # 2. Проверка SpeechRecognition
    print("\nИнициализация микрофона через SpeechRecognition...")
    try:
        m = sr.Microphone()
        print("Микрофон инициализирован.")
        
        r = sr.Recognizer()
        print("Калибровка микрофона (это может занять около 1 секунды)...")
        
        with m as source:
            r.adjust_for_ambient_noise(source, duration=1)
            print("Калибровка завершена успешно!")
            
        print("[УСПЕХ]: Микрофон готов к работе.")
    except Exception as e:
        print(f"[ОШИБКА SpeechRecognition/Микрофон]: {e}")

if __name__ == "__main__":
    test_audio()
