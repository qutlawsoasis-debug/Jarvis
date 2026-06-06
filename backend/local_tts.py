import os
import urllib.request
import wave
import sys

# Настройка кодировки для корректного вывода на русском языке в консоли Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

class LocalTTS:
    def __init__(self, model_name="ru_RU-dmitri-medium"):
        self.model_dir = os.path.join(os.path.dirname(__file__), "piper_models")
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.model_path = os.path.join(self.model_dir, f"{model_name}.onnx")
        self.config_path = os.path.join(self.model_dir, f"{model_name}.onnx.json")
        
        self.onnx_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ru/ru_RU/dmitri/medium/{model_name}.onnx"
        self.json_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ru/ru_RU/dmitri/medium/{model_name}.onnx.json"
        
        self._ensure_model_exists()
        
        try:
            from piper.voice import PiperVoice
            self.voice = PiperVoice.load(self.model_path)
            print(f"[LocalTTS] Успешно загружена модель Piper: {self.model_path}")
        except Exception as e:
            print(f"[LocalTTS] Ошибка при импорте или инициализации PiperVoice: {e}")
            self.voice = None

    def _ensure_model_exists(self):
        if not os.path.exists(self.model_path):
            print(f"[LocalTTS] Модель {self.model_path} не найдена. Начинаю скачивание...")
            try:
                urllib.request.urlretrieve(self.onnx_url, self.model_path)
                print(f"[LocalTTS] Скачана модель: {self.model_path}")
            except Exception as e:
                print(f"[LocalTTS] Ошибка скачивания модели: {e}")
                
        if not os.path.exists(self.config_path):
            print(f"[LocalTTS] Конфигурация {self.config_path} не найдена. Начинаю скачивание...")
            try:
                urllib.request.urlretrieve(self.json_url, self.config_path)
                print(f"[LocalTTS] Скачана конфигурация: {self.config_path}")
            except Exception as e:
                print(f"[LocalTTS] Ошибка скачивания конфигурации: {e}")

    def synthesize(self, text, output_file="response.wav"):
        if not self.voice:
            print("[LocalTTS] Движок Piper не инициализирован. Синтез невозможен.")
            return False
            
        try:
            # Piper voice synthesizes directly into a wave file
            with wave.open(output_file, "wb") as wav_file:
                self.voice.synthesize(text, wav_file)
            return True
        except Exception as e:
            print(f"[LocalTTS] Ошибка при синтезе речи Piper: {e}")
            return False
