import os
import sys
import time
import json
import threading
import pyaudio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Добавляем текущую директорию в пути импорта, чтобы правильно импортировать модули бэкенда
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_config_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "config.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

import jarvis_friend

app = FastAPI(title="Jarvis API Server")

# Разрешаем CORS, чтобы Electron-фронтенд мог делать запросы
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConfigSchema(BaseModel):
    GEMINI_API_KEY: str
    MIC_NAME: str
    WAKE_WORD: str = "джарвис"
    ACTIVE_TIMEOUT: int = 15
    TTS_ENGINE: str = "online"
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = ""
    FISH_API_KEY: str = ""
    FISH_VOICE_ID: str = ""

def get_microphones():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount', 0)
    mics = []
    
    # Добавляем устройство по умолчанию
    mics.append({"index": "Default", "name": "По умолчанию (Default)"})
    
    for i in range(numdevices):
        try:
            device_info = p.get_device_info_by_host_api_device_index(0, i)
            if device_info.get('maxInputChannels', 0) > 0:
                name = device_info.get('name', '')
                # Очистка имени от некорректных кодировок (корректно обрабатываем CP1252/CP1251)
                name_clean = name
                try:
                    name_clean = name.encode('cp1252').decode('cp1251')
                except Exception:
                    pass
                mics.append({"index": str(i), "name": name_clean})
        except Exception as e:
            print(f"[Server] Ошибка получения инфо об устройстве {i}: {e}")
            
    p.terminate()
    return mics

def restart_assistant_thread():
    if jarvis_friend.ASSISTANT_RUNNING:
        jarvis_friend.ASSISTANT_RUNNING = False
        # Ждем завершения потока
        for _ in range(30):
            if jarvis_friend.ASSISTANT_STATE == "stopped":
                break
            time.sleep(0.1)
            
    # Запуск нового потока
    jarvis_friend.ASSISTANT_RUNNING = True
    jarvis_friend.ASSISTANT_STATE = "thinking"
    jarvis_friend.ASSISTANT_ERROR = ""
    thread = threading.Thread(target=jarvis_friend.run_voice_assistant, daemon=True)
    thread.start()

@app.get("/api/mics")
def get_mics_endpoint():
    try:
        return get_microphones()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения аудиоустройств: {str(e)}")

@app.get("/api/config")
def get_config_endpoint():
    config_path = get_config_path()
    defaults = {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
        "MIC_NAME": "Default",
        "WAKE_WORD": os.getenv("WAKE_WORD", "джарвис"),
        "ACTIVE_TIMEOUT": int(os.getenv("ACTIVE_TIMEOUT", "15")),
        "TTS_ENGINE": os.getenv("TTS_ENGINE", "online"),
        "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY", ""),
        "ELEVENLABS_VOICE_ID": os.getenv("ELEVENLABS_VOICE_ID", ""),
        "FISH_API_KEY": os.getenv("FISH_API_KEY", ""),
        "FISH_VOICE_ID": os.getenv("FISH_VOICE_ID", "")
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Merge loaded config with defaults so no new key is ever missing
                for k, v in defaults.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка чтения файла конфигурации: {str(e)}")
    return defaults

@app.post("/api/config")
def save_config_endpoint(config: ConfigSchema):
    config_path = get_config_path()
    try:
        config_dict = config.dict()
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)
            
        # Автоматически перезапускаем поток ассистента с новыми настройками
        restart_assistant_thread()
        return {"status": "saved", "config": config_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения файла конфигурации: {str(e)}")

@app.get("/api/status")
def get_status_endpoint():
    return {
        "running": jarvis_friend.ASSISTANT_RUNNING,
        "state": jarvis_friend.ASSISTANT_STATE,
        "error": jarvis_friend.ASSISTANT_ERROR
    }

@app.post("/api/start")
def start_endpoint():
    if jarvis_friend.ASSISTANT_RUNNING and jarvis_friend.ASSISTANT_STATE != "error":
        return {"status": "already_running"}
    
    # Запускаем поток
    jarvis_friend.ASSISTANT_RUNNING = True
    jarvis_friend.ASSISTANT_STATE = "thinking"
    jarvis_friend.ASSISTANT_ERROR = ""
    thread = threading.Thread(target=jarvis_friend.run_voice_assistant, daemon=True)
    thread.start()
    return {"status": "started"}

@app.post("/api/stop")
def stop_endpoint():
    jarvis_friend.ASSISTANT_RUNNING = False
    jarvis_friend.ASSISTANT_STATE = "stopped"
    return {"status": "stopped"}

if __name__ == "__main__":
    # Запускаем FastAPI сервер
    print("[Server] Запуск API сервера на http://127.0.0.1:47720 ...")
    
    # Пробуем автоматически запустить ассистента, если в config.json есть ключ
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("GEMINI_API_KEY"):
                    print("[Server] Обнаружен API-ключ в config.json, автоматический запуск голосового ядра...")
                    jarvis_friend.ASSISTANT_RUNNING = True
                    thread = threading.Thread(target=jarvis_friend.run_voice_assistant, daemon=True)
                    thread.start()
        except Exception as e:
            print(f"[Server] Не удалось выполнить автозапуск ядра: {e}")
            
    uvicorn.run(app, host="127.0.0.1", port=47720)
