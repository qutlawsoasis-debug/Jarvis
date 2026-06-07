import os
import sys
import time
import json
import numpy as np
import pyaudio
import torch
from faster_whisper import WhisperModel
from silero_vad import load_silero_vad, VADIterator

class LocalSTT:
    def __init__(self, model_size="base", device="cpu", compute_type="int8", mic_name=None):
        """
        Инициализирует локальный движок распознавания речи.
        - model_size: 'tiny', 'base', 'small' (рекомендуется 'base' для баланса скорость/точность)
        - device: 'cpu' (для экономии ОЗУ/VRAM) или 'cuda'
        - compute_type: 'int8' (квантованная модель для максимальной скорости на CPU)
        """
        print(f"[LocalSTT] Инициализация Whisper (модель: {model_size}, устройство: {device}, тип: {compute_type})...")
        self.whisper = WhisperModel(model_size, device=device, compute_type=compute_type)
        
        print("[LocalSTT] Загрузка Silero VAD...")
        self.vad_model = load_silero_vad()
        
        # Настройка VADIterator. 
        # min_silence_duration_ms=600 означает, что речь считается законченной после 600мс тишины
        self.vad_iterator = VADIterator(
            self.vad_model, 
            threshold=0.5, 
            sampling_rate=16000, 
            min_silence_duration_ms=600
        )
        
        # Аудио-параметры
        self.sample_rate = 16000
        self.chunk_size = 512  # Фиксированный размер фрейма для Silero VAD
        self.pyaudio_format = pyaudio.paInt16
        self.p = pyaudio.PyAudio()
        
        # Загружаем имя микрофона из config.json, если не передано явно
        if mic_name is None:
            if getattr(sys, 'frozen', False):
                config_path = os.path.join(os.path.dirname(sys.executable), "config.json")
            else:
                config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                        mic_name = config_data.get("MIC_NAME", "Default")
                except Exception as e:
                    print(f"[LocalSTT] Ошибка чтения config.json: {e}")
                    mic_name = "Default"
            else:
                mic_name = "Default"
                
        # Настройка индекса микрофона
        if mic_name == "Default" or not mic_name:
            self.input_device_index = None
            print("[LocalSTT] Используется микрофон по умолчанию (Default).")
        else:
            self.input_device_index = self._find_device_index(mic_name)
        
        # Геймерский словарь для улучшения распознавания терминов и имен в играх
        self.initial_prompt = (
            "Джарвис, Rust, скрап, вайп, рейд, рт, кирка, копье, Minecraft, шкаф, спальник, "
            "идти вперед, прыгни, открой сайт, музыка, пауза, продолжи, стоп, громкость"
        )
        print("[LocalSTT] Локальный STT модуль успешно инициализирован.")

    def _find_device_index(self, name_pattern):
        """Находит индекс устройства ввода по подстроке имени или прямому индексу"""
        try:
            # Если передано число, используем его напрямую как индекс
            return int(name_pattern)
        except ValueError:
            pass
            
        num_devices = self.p.get_device_count()
        # Ищем совпадение по подстроке в названиях устройств ввода
        for i in range(num_devices):
            try:
                device_info = self.p.get_device_info_by_index(i)
                if device_info.get('maxInputChannels', 0) > 0:
                    dev_name = device_info.get('name', '')
                    
                    # Декодируем имя на случай если оно пришло в некорректной кодировке CP1252
                    dev_name_clean = dev_name
                    try:
                        dev_name_clean = dev_name.encode('cp1252').decode('cp1251')
                    except Exception:
                        pass
                        
                    if name_pattern.lower() in dev_name_clean.lower() or name_pattern.lower() in dev_name.lower():
                        print(f"[LocalSTT] Найдено аудиоустройство '{dev_name_clean}' на индексе {i}")
                        return i
            except Exception as e:
                print(f"[LocalSTT] Ошибка опроса устройства {i}: {e}")
                
        # Если устройство не найдено
        raise ValueError(f"Микрофон '{name_pattern}' не найден в системе. Подключите устройство.")

    def listen_and_transcribe(self, listen_timeout=7, phrase_time_limit=15):
        """
        Слушает микрофон, выделяет речь с помощью Silero VAD в реальном времени (в памяти)
        и отправляет в faster-whisper для мгновенного распознавания.
        
        listen_timeout: Время ожидания начала речи в секундах
        phrase_time_limit: Максимальная длительность одной фразы в секундах
        """
        # Сброс состояний VAD для новой фразы
        self.vad_iterator.reset_states()
        
        # Открываем поток микрофона
        stream = self.p.open(
            format=self.pyaudio_format,
            channels=1,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.input_device_index,
            frames_per_buffer=self.chunk_size
        )
        
        print("[LocalSTT] Слушаю...")
        
        speaking = False
        audio_buffer = []
        
        start_wait_time = time.time()
        phrase_start_time = None
        
        try:
            while True:
                # Читаем сырые байты из микрофона
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                except IOError:
                    # В случае переполнения буфера пропускаем чанк
                    continue
                
                # Конвертируем в float32 numpy array, нормализованный в [-1.0, 1.0]
                audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                tensor_chunk = torch.from_numpy(audio_chunk)
                
                # Проверяем VAD
                vad_out = self.vad_iterator(tensor_chunk)
                
                current_time = time.time()
                
                # Обработка состояний речи
                if vad_out is not None:
                    if 'start' in vad_out:
                        print("[LocalSTT] Обнаружено начало речи...")
                        speaking = True
                        phrase_start_time = current_time
                        
                    elif 'end' in vad_out and speaking:
                        print("[LocalSTT] Речь завершена (обнаружена тишина).")
                        break
                
                # Если пользователь уже говорит
                if speaking:
                    audio_buffer.append(audio_chunk)
                    # Лимит времени на фразу
                    if current_time - phrase_start_time > phrase_time_limit:
                        print("[LocalSTT] Превышен лимит времени на фразу.")
                        break
                else:
                    # Таймаут ожидания фразы
                    if current_time - start_wait_time > listen_timeout:
                        print("[LocalSTT] Таймаут ожидания речи.")
                        break
                        
        finally:
            # Закрываем поток
            stream.stop_stream()
            stream.close()
            
        # Если ничего не записали
        if not audio_buffer:
            return ""
            
        # Соединяем все записанные чанки из ОЗУ в один массив
        full_audio = np.concatenate(audio_buffer)
        
        # Распознаем речь
        print("[LocalSTT] Распознавание...")
        t0 = time.time()
        segments, info = self.whisper.transcribe(
            full_audio, 
            beam_size=5, 
            initial_prompt=self.initial_prompt,
            language="ru"
        )
        
        # Собираем текст из сегментов
        text = "".join([segment.text for segment in segments]).strip()
        transcribe_time = time.time() - t0
        print(f"[STT] Речь распознана за {transcribe_time:.2f} секунд")
        print(f"[LocalSTT] Распознано: '{text}' (Язык: {info.language}, точность: {info.language_probability:.2f})")
        
        return text

    def close(self):
        """Освобождает ресурсы PyAudio"""
        self.p.terminate()

if __name__ == "__main__":
    # Код для тестирования модуля
    stt = LocalSTT(model_size="base")
    try:
        while True:
            print("\nГоворите (Нажмите Ctrl+C для выхода)...")
            result = stt.listen_and_transcribe()
            if result:
                print(f"Результат: {result}")
    except KeyboardInterrupt:
        print("\nВыход.")
    finally:
        stt.close()
