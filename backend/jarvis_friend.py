import os
import sys
import time
import json
import asyncio
import threading
import requests
import ctypes
import winsound
import edge_tts
from local_stt import LocalSTT
from dotenv import load_dotenv

# Подключаем модуль инструментов
from tools import AVAILABLE_TOOLS, GEMINI_TOOLS_DECLARATION, retrieve_memory_list

# Настройка кодировки для корректного вывода на русском языке в консоли Windows
if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr is not None and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Класс для дублирования вывода консоли в лог-файл
class Logger(object):
    def __init__(self, filename=None):
        self.terminal = sys.stdout
        if filename is None:
            filename = os.path.join(os.path.dirname(__file__), "jarvis.log")
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        if self.terminal is not None:
            try:
                self.terminal.write(message)
            except Exception:
                pass
        self.log.write(message)
        self.log.flush()

    def flush(self):
        if self.terminal is not None and hasattr(self.terminal, 'flush'):
            try:
                self.terminal.flush()
            except Exception:
                pass
        self.log.flush()

    def isatty(self):
        if self.terminal is not None and hasattr(self.terminal, 'isatty'):
            try:
                return self.terminal.isatty()
            except Exception:
                pass
        return False

sys.stdout = Logger()
sys.stderr = Logger(os.path.join(os.path.dirname(__file__), "jarvis.log"))

# Загружаем настройки из .env
if getattr(sys, 'frozen', False):
    load_dotenv(os.path.join(os.path.dirname(sys.executable), '.env'))
else:
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# Настройки по умолчанию
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
WAKE_WORD = os.getenv("WAKE_WORD", "джарвис").lower().strip()
VOICE = os.getenv("VOICE", "ru-RU-DmitryNeural")  # Премиальный мужской голос
ACTIVE_TIMEOUT = int(os.getenv("ACTIVE_TIMEOUT", "15"))  # Время активного диалога в секундах
MODEL_NAME = os.getenv("MODEL", "gemini-3.1-flash-lite")
TTS_ENGINE = os.getenv("TTS_ENGINE", "local").lower().strip()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
XTTS_SPEAKER = os.getenv("XTTS_SPEAKER", "patrick.wav").strip()
FISH_API_KEY = os.getenv("FISH_API_KEY", "").strip()
FISH_VOICE_ID = os.getenv("FISH_VOICE_ID", "").strip()
MIC_INDEX = os.getenv("MIC_INDEX", "")
MIC_INDEX = int(MIC_INDEX) if MIC_INDEX.strip() else None
ENERGY_THRESHOLD = os.getenv("ENERGY_THRESHOLD", "300")
ENERGY_THRESHOLD = int(ENERGY_THRESHOLD) if ENERGY_THRESHOLD.strip() else 300
ADJUST_AMBIENT = os.getenv("ADJUST_AMBIENT", "True").strip().lower() == "true"

# Переменные управления состоянием для API/Electron
ASSISTANT_RUNNING = False
ASSISTANT_STATE = "stopped"  # stopped, idle, listening, thinking, speaking, error
ASSISTANT_ERROR = ""

# Глобальная очередь для GUI-сигналов
GUI_QUEUE = None

local_speaker = None
if TTS_ENGINE in ["local", "local_sapi5", "elevenlabs"]:
    try:
        import pyttsx3
        local_speaker = pyttsx3.init()
        voices = local_speaker.getProperty('voices')
        for voice in voices:
            if "russian" in voice.name.lower() or "ru-ru" in voice.id.lower() or "irina" in voice.name.lower():
                local_speaker.setProperty('voice', voice.id)
                break
        local_speaker.setProperty('rate', 190)  # Слегка ускоряем речь для динамики
    except Exception as e:
        print(f"[Ошибка инициализации локального спикера]: {e}")

def load_system_instruction():
    profile_path = os.path.join(os.path.dirname(__file__), 'user_profile.json')
    user_name = "Мирон"
    user_title = "создатель"
    user_info = "Владелец этого компьютера, разработчик."
    personality = "Преданный, харизматичный, с тонким английским юмором и иронией."
    
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                user_name = data.get("user_name", user_name)
                user_title = data.get("user_title", user_title)
                user_info = data.get("user_info", user_info)
                personality = data.get("assistant_personality", personality)
        except Exception as e:
            print(f"Ошибка загрузки профиля: {e}")
            
    instruction = (
        f"Ты — Джарвис, близкий друг и преданный голосовой ассистент пользователя в стиле дворецкого Тони Старка из Железного Человека. "
        f"Ты общаешься с пользователем по имени {user_name} (обращайся к нему как '{user_title}').\n"
        f"Информация о пользователе: {user_info}\n"
        f"Твой характер: {personality}\n\n"
        "ИГРОВЫЕ ВОЗМОЖНОСТИ:\n"
        "Ты можешь играть в компьютерные игры (например, Rust или Minecraft) вместе с создателем! "
        "У тебя есть инструменты `game_action` (для разовых команд, таких как движение вперед, назад, прыжки, удары, обзор) и `autonomous_play` (для запуска полноценного цикла автономной игры, где ты делаешь скриншоты, анализируешь ситуацию и сам принимаешь решения).\n"
        "Если создатель просит тебя 'поиграй со мной', 'начни автономную игру', 'беги вперед', 'прыгни', 'повернись' или выполнить любые другие игровые действия, ты ОБЯЗАТЕЛЬНО должен вызвать соответствующий инструмент (`game_action` или `autonomous_play`). "
        "НИКОГДА не отказывайся и не говори, что ты всего лишь ИИ, голос или не умеешь играть — у тебя есть прямой доступ к клавиатуре и мыши через DirectInput скан-коды и ты умеешь анализировать игровой экран!\n\n"
        "ПРАВИЛА ДЛЯ УСТНОЙ РЕЧИ:\n"
        "1. Твои ответы будут озвучены синтезатором речи. Отвечай кратко, естественно и лаконично (1-3 коротких предложения), как в реальном живом разговоре. Избегай длинных монологов.\n"
        "2. НИКОГДА не используй форматирование текста и markdown-разметку (списки, жирный шрифт, символы '*', '#', таблицы, ссылки). Если нужно перечислить пункты, говори обычным текстом.\n"
        "3. Никогда не читай и не произноси программный код в речевом ответе. Если ты написал код или создал файл через инструменты, просто скажи: 'Код написан и сохранен в файл, создатель' или 'Скрипт успешно выполнен'.\n"
        "4. Если пользователь просит тебя выполнить действие на ПК (открыть сайт, запустить команду, изменить громкость, найти информацию в интернете, прочитать или создать файл, управлять персонажем в игре), ВСЕГДА используй соответствующий инструмент (tool) и кратко озвучь результат выполнения."
    )
    return instruction

# Системная инструкция для ИИ
SYSTEM_INSTRUCTION = load_system_instruction()

# Хранилище контекста диалога
chat_history = []
MAX_HISTORY_LEN = 20

def save_to_history(role, parts):
    global chat_history
    chat_history.append({"role": role, "parts": parts})
    if len(chat_history) > MAX_HISTORY_LEN:
        chat_history = chat_history[-MAX_HISTORY_LEN:]

async def generate_voice(text, filename="response.mp3"):
    """Генерирует MP3 файл из текста с помощью Microsoft Edge TTS с повышенным темпом речи"""
    try:
        communicate = edge_tts.Communicate(text, VOICE, rate="+15%")
        await communicate.save(filename)
        return True
    except Exception as e:
        print(f"[Ошибка Edge-TTS]: {e}")
        return False

from ctypes import wintypes
try:
    ctypes.windll.winmm.mciSendStringW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.UINT, wintypes.HANDLE]
    ctypes.windll.winmm.mciSendStringW.restype = wintypes.DWORD
except Exception as e:
    print(f"[Ctypes Init Error for mciSendStringW]: {e}")

def play_audio(filename="response.mp3"):
    """Воспроизводит аудиофайл: WAV через winsound, MP3 через Windows MCI"""
    try:
        abs_path = os.path.abspath(filename)
        if filename.lower().endswith('.wav'):
            winsound.PlaySound(abs_path, winsound.SND_FILENAME)
        else:
            ctypes.windll.winmm.mciSendStringW(f'open "{abs_path}" alias my_sound', None, 0, 0)
            ctypes.windll.winmm.mciSendStringW('play my_sound wait', None, 0, 0)
            ctypes.windll.winmm.mciSendStringW('close my_sound', None, 0, 0)
    except Exception as e:
        print(f"[Ошибка воспроизведения звука]: {e}")

def generate_voice_elevenlabs(text, filename="response.mp3"):
    """Генерирует MP3 файл из текста с помощью ElevenLabs API (для клонированного голоса)"""
    global ASSISTANT_ERROR, ASSISTANT_STATE, ASSISTANT_RUNNING
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            return True
        else:
            print(f"[ElevenLabs API Ошибка {response.status_code}]: {response.text}")
            error_msg = f"Ошибка ElevenLabs ({response.status_code})"
            try:
                err_data = response.json()
                if "detail" in err_data:
                    detail = err_data["detail"]
                    if isinstance(detail, dict):
                        status = detail.get("status", "")
                        message = detail.get("message", "")
                        if status == "missing_permissions":
                            error_msg = "ElevenLabs: API-ключ не имеет разрешения text_to_speech. Проверьте настройки ключа в ElevenLabs."
                        elif message:
                            error_msg = f"ElevenLabs: {message}"
                    else:
                        error_msg = f"ElevenLabs: {detail}"
            except Exception:
                if response.status_code == 401:
                    error_msg = "ElevenLabs: Неверный API-ключ (401 Unauthorized)."
                elif response.status_code == 404:
                    error_msg = "ElevenLabs: Голос не найден (404 Not Found)."
            
            ASSISTANT_ERROR = error_msg
            ASSISTANT_STATE = "error"
            ASSISTANT_RUNNING = False
            return False
    except Exception as e:
        print(f"[ElevenLabs Ошибка соединения]: {e}")
        ASSISTANT_ERROR = f"ElevenLabs: Ошибка соединения: {str(e)}"
        ASSISTANT_STATE = "error"
        ASSISTANT_RUNNING = False
        return False

def generate_voice_fish(text, filename="response.mp3"):
    """Генерирует MP3 файл из текста с помощью Fish Audio API"""
    global ASSISTANT_ERROR, ASSISTANT_STATE, ASSISTANT_RUNNING
    url = "https://api.fish.audio/v1/tts"
    headers = {
        "Authorization": f"Bearer {FISH_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "reference_id": FISH_VOICE_ID
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            return True
        else:
            print(f"[Fish Audio API Ошибка {response.status_code}]: {response.text}")
            error_msg = f"Ошибка Fish Audio ({response.status_code})"
            try:
                err_data = response.json()
                if "detail" in err_data:
                    error_msg = f"Fish Audio: {err_data['detail']}"
                elif "message" in err_data:
                    error_msg = f"Fish Audio: {err_data['message']}"
            except Exception:
                if response.status_code == 401:
                    error_msg = "Fish Audio: Неверный API-ключ (401 Unauthorized)."
                elif response.status_code == 404:
                    error_msg = "Fish Audio: Референсный голос не найден (404 Not Found)."
            
            ASSISTANT_ERROR = error_msg
            ASSISTANT_STATE = "error"
            ASSISTANT_RUNNING = False
            return False
    except Exception as e:
        print(f"[Fish Audio Ошибка соединения]: {e}")
        ASSISTANT_ERROR = f"Fish Audio: Ошибка соединения: {str(e)}"
        ASSISTANT_STATE = "error"
        ASSISTANT_RUNNING = False
        return False

local_tts_engine = None

def get_local_tts_engine():
    global local_tts_engine
    if local_tts_engine is None:
        try:
            from local_tts import LocalTTS
            local_tts_engine = LocalTTS()
        except Exception as e:
            print(f"[Ошибка инициализации LocalTTS (Piper)]: {e}")
    return local_tts_engine


def speak(text):
    """Озвучивает текст: использует local_xtts, ElevenLabs, оффлайн SAPI5 или онлайн Edge-TTS"""
    global ASSISTANT_STATE, ASSISTANT_ERROR, ASSISTANT_RUNNING
    ASSISTANT_STATE = "speaking"
    print(f"[Джарвис]: {text}")
    clean_text = text.replace("*", "").replace("#", "").strip()
    if not clean_text:
        return
        
    global GUI_QUEUE
    if GUI_QUEUE is not None:
        GUI_QUEUE.put({"type": "state", "value": "speaking"})
        GUI_QUEUE.put({"type": "jarvis_text", "value": clean_text})
        
    try:
        # Проверяем кэш для аудиофайлов (не кэшируем для legacy SAPI5)
        use_cache = len(clean_text) < 100 and TTS_ENGINE != "local_sapi5"
        cache_file = None
        
        if use_cache:
            import hashlib
            if TTS_ENGINE in ["local", "local_xtts"]:
                voice_id = "piper_dmitri"
                ext = "wav"
            elif TTS_ENGINE == "fishaudio":
                voice_id = FISH_VOICE_ID
                ext = "mp3"
            elif TTS_ENGINE == "elevenlabs":
                voice_id = ELEVENLABS_VOICE_ID
                ext = "mp3"
            else:
                voice_id = VOICE
                ext = "mp3"
                
            hash_input = f"{voice_id}_{clean_text.lower()}"
            md5_hash = hashlib.md5(hash_input.encode('utf-8')).hexdigest()
            cache_dir = os.path.join(os.path.dirname(__file__), "output", "voice_cache")
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = os.path.join(cache_dir, f"{md5_hash}.{ext}")
            
            if os.path.exists(cache_file):
                print(f"[Кэш голоса] Воспроизведение из кэша: {cache_file}")
                play_audio(cache_file)
                return

        if TTS_ENGINE in ["local", "local_xtts"]:
            filename = cache_file if use_cache else "response.wav"
            try:
                if os.path.exists(filename) and not use_cache:
                    os.remove(filename)
            except:
                pass
            
            success = False
            engine = get_local_tts_engine()
            if engine:
                success = engine.synthesize(clean_text, filename)
                
            if success:
                play_audio(filename)
            else:
                print("[Local Piper TTS сбой] Переключение на резервный Edge-TTS голос...")
                filename_mp3 = "response.mp3"
                try:
                    if os.path.exists(filename_mp3):
                        os.remove(filename_mp3)
                except:
                    pass
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success_edge = loop.run_until_complete(generate_voice(clean_text, filename_mp3))
                loop.close()
                if success_edge:
                    play_audio(filename_mp3)
                elif local_speaker:
                    print("[Edge-TTS сбой] Переключение на локальный резервный голос SAPI5...")
                    try:
                        local_speaker.say(clean_text)
                        local_speaker.runAndWait()
                    except Exception as e:
                        print(f"[Ошибка локального синтеза]: {e}")
                        
        elif TTS_ENGINE == "fishaudio":
            if not FISH_API_KEY or not FISH_VOICE_ID:
                ASSISTANT_ERROR = "Fish Audio: API-ключ или Voice ID не заполнены в настройках."
                ASSISTANT_STATE = "error"
                ASSISTANT_RUNNING = False
                return
            
            filename = cache_file if use_cache else "response.mp3"
            try:
                if os.path.exists(filename) and not use_cache:
                    os.remove(filename)
            except:
                pass
            
            success = generate_voice_fish(clean_text, filename)
            if success:
                play_audio(filename)
            else:
                return
                
        elif TTS_ENGINE == "elevenlabs":
            if not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
                ASSISTANT_ERROR = "ElevenLabs: API-ключ или Voice ID не заполнены в настройках."
                ASSISTANT_STATE = "error"
                ASSISTANT_RUNNING = False
                return
            
            filename = cache_file if use_cache else "response.mp3"
            try:
                if os.path.exists(filename) and not use_cache:
                    os.remove(filename)
            except:
                pass
            
            success = generate_voice_elevenlabs(clean_text, filename)
            if success:
                play_audio(filename)
            else:
                return
        elif TTS_ENGINE == "local_sapi5" and local_speaker:
            try:
                local_speaker.say(clean_text)
                local_speaker.runAndWait()
            except Exception as e:
                print(f"[Ошибка локального синтеза речи (SAPI5)]: {e}")
        else:
            filename = cache_file if use_cache else "response.mp3"
            try:
                if os.path.exists(filename) and not use_cache:
                    os.remove(filename)
            except:
                pass
                
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(generate_voice(clean_text, filename))
            loop.close()
            
            if success:
                play_audio(filename)
    finally:
        ASSISTANT_STATE = "thinking"
        if GUI_QUEUE is not None:
            GUI_QUEUE.put({"type": "state", "value": "thinking"})

def call_gemini_api(payload):
    """Выполняет HTTP-запрос к Gemini API"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[API Ошибка {response.status_code}]: {response.text}")
            return None
    except Exception as e:
        print(f"[API Ошибка соединения]: {e}")
        return None

def sanitize_chat_history(history):
    """Санирует историю диалога перед отправкой в Gemini API, чтобы не нарушать правила чередования ходов и вызовов функций."""
    sanitized = []
    for turn in history:
        role = turn.get("role")
        parts = turn.get("parts", [])
        
        # Пропускаем пустые ходы
        if not parts:
            continue
            
        # Убедимся, что первый ход — всегда от пользователя
        if not sanitized and role != "user":
            continue
            
        # Если в истории идут два одинаковых роля подряд, объединяем их части
        if sanitized and sanitized[-1]["role"] == role:
            new_parts = list(sanitized[-1]["parts"])
            for p in parts:
                new_parts.append(p)
            sanitized[-1]["parts"] = new_parts
        else:
            sanitized.append({"role": role, "parts": list(parts)})
            
    # Также убедимся, что первый ход не является ответом функции без предшествующего пользовательского текста
    # (если мы обрезали историю так, что остался только functionResponse)
    while sanitized:
        first_parts = sanitized[0]["parts"]
        has_only_func_response = any("functionResponse" in p for p in first_parts)
        if has_only_func_response:
            sanitized.pop(0)
            if sanitized and sanitized[0]["role"] != "user":
                sanitized.pop(0)
        else:
            break
            
    return sanitized

def process_ai_interaction(prompt):
    """Управляет циклом взаимодействия с ИИ (включая многократные вызовы инструментов)"""
    global chat_history, GUI_QUEUE
    
    # Бэкапим историю на случай ошибки в процессе транзакции
    history_backup = list(chat_history)
    
    # Обновляем GUI
    if GUI_QUEUE is not None:
        GUI_QUEUE.put({"type": "user_text", "value": prompt})
        GUI_QUEUE.put({"type": "state", "value": "thinking"})
        
    try:
        # Извлекаем воспоминания из долговременной памяти по семантическому сходству
        memories = []
        words = prompt.lower().split()
        keywords = ["вперед", "назад", "влево", "вправо", "прыгни", "присядь", "нажми", "кликни", "посмотри", "пауза", "продолжи", "стоп", "музыка", "включи", "песня", "сайт", "открой", "громкость", "выключи", "играй", "поиграем", "игра"]
        should_bypass = len(words) < 3 or any(kw in prompt.lower() for kw in keywords)
        
        if should_bypass:
            print("[Память Джарвиса] Пропуск RAG-памяти для быстрого выполнения команды.")
        else:
            try:
                memories = retrieve_memory_list(prompt, top_n=3)
            except Exception as ex:
                print(f"[Ошибка извлечения воспоминаний]: {ex}")
            
        memory_context = ""
        if memories:
            memory_context = "\n\nДополнительный контекст о создателе из памяти:\n" + "\n".join([f"- {m['key']}: {m['value']}" for m in memories])
            print(f"[Память Джарвиса] Подгружено {len(memories)} воспоминаний.")
            
        # Добавляем реплику пользователя
        save_to_history("user", [{"text": prompt}])
        
        # Собираем payload для запроса к Gemini с динамическим контекстом памяти
        payload = {
            "systemInstruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION + memory_context}]
            },
            "contents": sanitize_chat_history(chat_history),
            "tools": [{"functionDeclarations": GEMINI_TOOLS_DECLARATION}]
        }
        
        success = False
        # Цикл обработки (до тех пор, пока модель запрашивает инструменты)
        for step in range(5):
            print(f"[Джарвис думает...] (шаг {step + 1})")
            if GUI_QUEUE is not None:
                GUI_QUEUE.put({"type": "state", "value": "thinking"})
                
            response_json = call_gemini_api(payload)
            
            if not response_json or 'candidates' not in response_json:
                speak("Произошла ошибка связи с сервером ИИ, создатель.")
                break
                
            candidate = response_json['candidates'][0]
            content = candidate.get('content', {})
            parts = content.get('parts', [])
            
            if not parts:
                speak("Я не знаю, что ответить на это, создатель.")
                break
                
            # Сохраняем ответ модели в историю
            save_to_history("model", parts)
            
            # Проверяем, есть ли запрос на вызов функции
            function_calls = [p.get('functionCall') for p in parts if p.get('functionCall')]
            
            if not function_calls:
                # Если вызовов функций нет, значит это финальный текстовый ответ
                text_response = "".join([p.get('text', '') for p in parts if p.get('text')])
                if text_response:
                    speak(text_response)
                success = True
                return
                
            # Если есть вызов функции (инструмента)
            func_call = function_calls[0]
            name = func_call.get('name')
            args = func_call.get('args', {})
            
            print(f"[Запрос вызова инструмента]: {name}({args})")
            
            # Выполняем инструмент локально
            if name in AVAILABLE_TOOLS:
                tool_func = AVAILABLE_TOOLS[name]
                try:
                    tool_result = tool_func(**args)
                except Exception as e:
                    tool_result = f"Ошибка при выполнении инструмента: {str(e)}"
            else:
                tool_result = f"Ошибка: Инструмент {name} не поддерживается."
                
            print(f"[Результат инструмента]: {tool_result}")
            
            # Добавляем результат выполнения инструмента в историю для следующего шага
            function_response_part = {
                "functionResponse": {
                    "name": name,
                    "response": {"output": tool_result}
                }
            }
            save_to_history("user", [function_response_part])
            
            # Обновляем payload с учетом новых записей в истории
            payload["contents"] = sanitize_chat_history(chat_history)
 
        if not success:
            chat_history = history_backup
            
    except Exception as e:
        print(f"[Ошибка работы агента]: {e}")
        chat_history = history_backup
        speak("Произошла критическая ошибка взаимодействия с ИИ, создатель.")

def run_voice_assistant(gui_queue=None):
    global GUI_QUEUE, GEMINI_API_KEY, WAKE_WORD, ACTIVE_TIMEOUT, TTS_ENGINE
    global ASSISTANT_RUNNING, ASSISTANT_STATE, ASSISTANT_ERROR
    global ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, FISH_API_KEY, FISH_VOICE_ID
    
    GUI_QUEUE = gui_queue
    ASSISTANT_RUNNING = True
    ASSISTANT_ERROR = ""
    ASSISTANT_STATE = "thinking"
    
    # Загружаем настройки из config.json
    if getattr(sys, 'frozen', False):
        config_path = os.path.join(os.path.dirname(sys.executable), "config.json")
    else:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                GEMINI_API_KEY = config_data.get("GEMINI_API_KEY", "")
                WAKE_WORD = config_data.get("WAKE_WORD", "джарвис").lower().strip()
                ACTIVE_TIMEOUT = int(config_data.get("ACTIVE_TIMEOUT", 15))
                TTS_ENGINE = config_data.get("TTS_ENGINE", "online").lower().strip()
                mic_name = config_data.get("MIC_NAME", "Default")
                
                # Загружаем API ключи и Voice ID для премиум-голосов
                ELEVENLABS_API_KEY = config_data.get("ELEVENLABS_API_KEY", "")
                ELEVENLABS_VOICE_ID = config_data.get("ELEVENLABS_VOICE_ID", "")
                FISH_API_KEY = config_data.get("FISH_API_KEY", "")
                FISH_VOICE_ID = config_data.get("FISH_VOICE_ID", "")
        except Exception as e:
            print(f"[КРИТИЧЕСКАЯ ОШИБКА]: Ошибка чтения config.json: {e}")
            ASSISTANT_STATE = "error"
            ASSISTANT_ERROR = f"Ошибка чтения конфигурации: {str(e)}"
            ASSISTANT_RUNNING = False
            return
    else:
        print("[КРИТИЧЕСКАЯ ОШИБКА]: Файл config.json не найден!")
        ASSISTANT_STATE = "error"
        ASSISTANT_ERROR = "Конфигурационный файл config.json не найден."
        ASSISTANT_RUNNING = False
        return
        
    if not GEMINI_API_KEY:
        print("[КРИТИЧЕСКАЯ ОШИБКА]: В файле config.json отсутствует GEMINI_API_KEY!")
        ASSISTANT_STATE = "error"
        ASSISTANT_ERROR = "GEMINI_API_KEY отсутствует в конфигурации."
        ASSISTANT_RUNNING = False
        return
        
    # Инициализируем локальный STT (Silero VAD + faster-whisper base int8)
    try:
        stt = LocalSTT(model_size="base", device="cpu", compute_type="int8", mic_name=mic_name)
    except Exception as e:
        print(f"[КРИТИЧЕСКАЯ ОШИБКА]: Ошибка инициализации STT: {e}")
        ASSISTANT_STATE = "error"
        ASSISTANT_ERROR = str(e)
        ASSISTANT_RUNNING = False
        return
        
    print("==================================================")
    print("      ДЖАРВИС: ГОЛОСОВОЙ СОБЕСЕДНИК И ДРУГ        ")
    print("==================================================")
    print(f"Активационная фраза: '{WAKE_WORD.upper()}'")
    print("==================================================")
    
    profile_path = os.path.join(os.path.dirname(__file__), 'user_profile.json')
    user_title = "создатель"
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                user_title = data.get("user_title", "создатель")
        except:
            pass
            
    # Сигнализируем запуск озвучки
    if GUI_QUEUE is not None:
        GUI_QUEUE.put({"type": "state", "value": "speaking"})
        
    ASSISTANT_STATE = "speaking"
    speak(f"Системы инициализированы. Я на связи, {user_title}.")
    
    ASSISTANT_STATE = "idle"
    if GUI_QUEUE is not None:
        GUI_QUEUE.put({"type": "state", "value": "idle"})
        
    active_until = 0.0  # Время, до которого мы находимся в режиме активного диалога
    
    # Обернем цикл в глобальный try-except для защиты от падений
    while ASSISTANT_RUNNING:
        try:
            current_time = time.time()
            is_active_mode = current_time < active_until
            
            # Уведомляем GUI и API о текущем состоянии
            state_val = "listening" if is_active_mode else "idle"
            ASSISTANT_STATE = state_val
            if GUI_QUEUE is not None:
                GUI_QUEUE.put({"type": "state", "value": state_val})
                
            state_label = "[АКТИВНЫЙ РЕЖИМ БЕСЕДЫ]" if is_active_mode else "[ОЖИДАНИЕ АКТИВАЦИИ]"
            print(f"\n{state_label} Слушаю...")
            
            # Переходим в состояние распознавания в GUI и API
            if GUI_QUEUE is not None:
                GUI_QUEUE.put({"type": "state", "value": "listening"})
            ASSISTANT_STATE = "listening"
            
            listen_timeout = 8 if is_active_mode else 7
            
            # Локальное распознавание речи (Silero VAD + faster-whisper)
            text = stt.listen_and_transcribe(listen_timeout=listen_timeout, phrase_time_limit=8)
            
            # Если текст пустой, проверяем тайм-аут
            if not text:
                if is_active_mode:
                    print("Активный режим завершен по таймауту.")
                    if GUI_QUEUE is not None:
                        GUI_QUEUE.put({"type": "state", "value": "speaking"})
                    speak("Я перехожу в режим ожидания, создатель. Позовите, если понадоблюсь.")
                    if GUI_QUEUE is not None:
                        GUI_QUEUE.put({"type": "state", "value": "idle"})
                    active_until = 0.0
                continue
                
            # Переходим в состояние обработки в GUI и API
            if GUI_QUEUE is not None:
                GUI_QUEUE.put({"type": "state", "value": "thinking"})
            ASSISTANT_STATE = "thinking"
                
            print(f"Вы сказали: '{text}'")
            
            text_lower = text.lower()
            
            if is_active_mode:
                if any(word in text_lower for word in ["пока", "прощай", "отключись", "стоп", "хватит"]):
                    if GUI_QUEUE is not None:
                        GUI_QUEUE.put({"type": "user_text", "value": text})
                        GUI_QUEUE.put({"type": "state", "value": "speaking"})
                    speak("До связи, создатель. Я на приёме.")
                    if GUI_QUEUE is not None:
                        GUI_QUEUE.put({"type": "state", "value": "idle"})
                    active_until = 0.0
                else:
                    active_until = time.time() + ACTIVE_TIMEOUT
                    process_ai_interaction(text)
            else:
                if WAKE_WORD in text_lower:
                    idx = text_lower.find(WAKE_WORD)
                    command = text[idx + len(WAKE_WORD):].strip()
                    active_until = time.time() + ACTIVE_TIMEOUT
                    
                    if command:
                        process_ai_interaction(command)
                    else:
                        if GUI_QUEUE is not None:
                            GUI_QUEUE.put({"type": "user_text", "value": text})
                            GUI_QUEUE.put({"type": "state", "value": "speaking"})
                        speak("Слушаю вас, создатель.")
                        if GUI_QUEUE is not None:
                            GUI_QUEUE.put({"type": "state", "value": "listening"})
                        active_until = time.time() + ACTIVE_TIMEOUT
        except Exception as e:
            print(f"Голосовой цикл Джарвиса прервался ошибкой: {e}")
            if GUI_QUEUE is not None:
                GUI_QUEUE.put({"type": "state", "value": "speaking"})
            speak("Прошу прощения, создатель, произошел небольшой программный сбой, я перезапускаю системы.")
            if GUI_QUEUE is not None:
                GUI_QUEUE.put({"type": "state", "value": "idle"})
            time.sleep(2)
            
    # Уведомляем о завершении работы
    ASSISTANT_STATE = "stopped"
    print("[Core] Голосовой цикл Джарвиса остановлен.")

def main():
    run_voice_assistant(None)

if __name__ == "__main__":
    import socket
    import sys
    try:
        _instance_lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _instance_lock.bind(('127.0.0.1', 47719))
        _instance_lock.listen(1)
    except socket.error:
        print("Джарвис уже запущен в другом процессе! Выходим.")
        sys.exit(0)
        
    main()
