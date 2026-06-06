import ctypes
import os
import asyncio
import edge_tts

def get_mci_error(error_code):
    if error_code == 0:
        return "Успешно"
    buffer = ctypes.create_unicode_buffer(256)
    ctypes.windll.winmm.mciGetErrorStringW(error_code, buffer, 256)
    return buffer.value

async def speak_and_test(text):
    print(f"Синтез речи: '{text}'...")
    communicate = edge_tts.Communicate(text, "ru-RU-DmitryNeural")
    await communicate.save("test_play.mp3")
    
    abs_path = os.path.abspath("test_play.mp3")
    print(f"Путь к файлу: {abs_path}")
    
    # Пытаемся принудительно закрыть алиас перед открытием
    ctypes.windll.winmm.mciSendStringW('close my_test_mp3', None, 0, 0)
    
    # 1. Открытие
    cmd_open = f'open "{abs_path}" type mpegvideo alias my_test_mp3'
    print(f"Команда: {cmd_open}")
    res_open = ctypes.windll.winmm.mciSendStringW(cmd_open, None, 0, 0)
    print(f"Результат открытия: {res_open} ({get_mci_error(res_open)})")
    
    # 2. Воспроизведение
    cmd_play = 'play my_test_mp3 wait'
    print(f"Команда: {cmd_play}")
    res_play = ctypes.windll.winmm.mciSendStringW(cmd_play, None, 0, 0)
    print(f"Результат воспроизведения: {res_play} ({get_mci_error(res_play)})")
    
    # 3. Закрытие
    cmd_close = 'close my_test_mp3'
    res_close = ctypes.windll.winmm.mciSendStringW(cmd_close, None, 0, 0)
    print(f"Результат закрытия: {res_close} ({get_mci_error(res_close)})")
    
    try:
        os.remove("test_play.mp3")
    except Exception as e:
        print(f"Не удалось удалить файл: {e}")

if __name__ == "__main__":
    asyncio.run(speak_and_test("Тест звуковой системы Джарвиса. Один, два, три."))
