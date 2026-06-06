import os
import subprocess
import webbrowser
import ctypes
import urllib.parse
import json
import requests
import time
import base64
import io
import math
from PIL import ImageGrab


def press_key(vk_code):
    """Нажимает и отпускает клавишу по её виртуальному коду (Virtual Key Code)"""
    try:
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)
        return True
    except Exception as e:
        print(f"Ошибка нажатия клавиши {vk_code}: {e}")
        return False

def press_keys(vk_codes):
    """Нажимает комбинацию клавиш (например, Ctrl+Tab)"""
    try:
        for vk in vk_codes:
            ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
            time.sleep(0.02)
        for vk in reversed(vk_codes):
            ctypes.windll.user32.keybd_event(vk, 0, 2, 0)
            time.sleep(0.02)
        return True
    except Exception as e:
        print(f"Ошибка нажатия клавиш {vk_codes}: {e}")
        return False

def run_terminal_command(command: str) -> str:
    """Запускает команду в PowerShell и возвращает консольный вывод.
    Пример: 'dir', 'ping google.com', 'pip list'
    """
    print(f"[Выполнение команды]: {command}")
    try:
        # Запускаем в powershell для лучшей совместимости
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=15
        )
        output = result.stdout.strip()
        errors = result.stderr.strip()
        
        response = ""
        if output:
            response += output
        if errors:
            if response:
                response += "\n\nОшибки:\n"
            response += errors
            
        if not response:
            return "Команда выполнена, но консольный вывод пуст."
            
        # Ограничиваем длину вывода, чтобы не перегружать контекст модели
        if len(response) > 2000:
            response = response[:2000] + "\n...[вывод обрезан из-за длины]..."
        return response
    except subprocess.TimeoutExpired:
        return "Ошибка: Превышено время ожидания выполнения команды (15 секунд)."
    except Exception as e:
        return f"Ошибка выполнения команды: {str(e)}"

def search_wikipedia(query: str) -> str:
    """Вспомогательная функция для поиска в Википедии при сбое основного поиска"""
    print(f"[Резервный поиск в Википедии]: {query}")
    headers = {
        "User-Agent": "JarvisAssistant/1.0 (contact: magne@gemini.antigravity)"
    }
    url = f"https://ru.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            search_results = data.get("query", {}).get("search", [])
            if search_results:
                import re
                snippets = []
                for res in search_results[:3]:
                    # Очищаем текст от HTML-тегов, которые возвращает API Википедии
                    snippet = re.sub(r'<[^>]*>', '', res.get("snippet", ""))
                    # Заменяем HTML-сущности
                    snippet = snippet.replace("&quot;", '"').replace("&amp;", '&').replace("lt;", '<').replace("gt;", '>')
                    snippets.append(f"- {res.get('title')}: {snippet}...")
                return "Результаты из Википедии:\n" + "\n\n".join(snippets)
            else:
                return "Поиск в Википедии также не дал результатов."
        return f"Ошибка Википедии (код {response.status_code})."
    except Exception as e:
        return f"Ошибка резервного поиска в Википедии: {str(e)}"

def search_web(query: str) -> str:
    """Ищет информацию в интернете через DuckDuckGo и возвращает краткие результаты.
    В случае блокировки запросов автоматически переключается на Википедию.
    Полезно для поиска новостей, погоды, фактов.
    """
    print(f"[Поиск в сети]: {query}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"[DuckDuckGo] Вернул код {response.status_code}. Переключение на Википедию.")
            return search_wikipedia(query)
            
        # Простой парсинг результатов без внешних библиотек BeautifulSoup
        from html.parser import HTMLParser
        
        class DDGParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.in_result = False
                self.in_snippet = False
                self.snippets = []
                self.current_snippet = []
                
            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                if tag == 'div' and 'result' in attrs_dict.get('class', ''):
                    self.in_result = True
                if self.in_result and tag == 'a' and 'result__snippet' in attrs_dict.get('class', ''):
                    self.in_snippet = True
                    self.current_snippet = []
                    
            def handle_endtag(self, tag):
                if tag == 'a' and self.in_snippet:
                    self.in_snippet = False
                    snippet_text = "".join(self.current_snippet).strip()
                    if snippet_text:
                        self.snippets.append(snippet_text)
                if tag == 'div' and self.in_result:
                    self.in_result = False
                    
            def handle_data(self, data):
                if self.in_snippet:
                    self.current_snippet.append(data)
                    
        parser = DDGParser()
        parser.feed(response.text)
        
        results = parser.snippets[:4]
        if not results:
            print("[DuckDuckGo] Результаты парсинга пусты. Переключение на Википедию.")
            return search_wikipedia(query)
            
        return "\n\n".join([f"- {res}" for res in results])
    except Exception as e:
        print(f"[DuckDuckGo Ошибка]: {str(e)}. Переключение на Википедию.")
        return search_wikipedia(query)

def open_website(url: str) -> str:
    """Открывает указанный URL-адрес в браузере по умолчанию.
    Примеры: 'https://youtube.com', 'https://google.com'
    """
    print(f"[Открытие сайта]: {url}")
    try:
        # Если не указан протокол, добавляем https
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        webbrowser.open(url)
        return f"Сайт {url} успешно открыт в браузере."
    except Exception as e:
        return f"Не удалось открыть сайт {url}: {str(e)}"

def write_file(filename: str, content: str) -> str:
    """Создает новый файл или перезаписывает существующий по указанному пути,
    записывая туда переданный контент. Полезно для написания кода или заметок.
    """
    print(f"[Запись в файл]: {filename}")
    try:
        # Убедимся, что записываем в безопасную директорию (разрешаем запись в scratch или текущую)
        # Если путь относительный, пишем в текущую рабочую директорию
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Файл {filename} успешно записан ({len(content)} символов)."
    except Exception as e:
        return f"Не удалось записать файл {filename}: {str(e)}"

def read_file(filename: str) -> str:
    """Читает содержимое файла и возвращает его в текстовом виде.
    Полезно для анализа логов или кода.
    """
    print(f"[Чтение файла]: {filename}")
    try:
        if not os.path.exists(filename):
            return f"Ошибка: Файл {filename} не существует."
        with open(filename, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(10000) # Читаем максимум 10к символов
            if len(content) >= 10000:
                content += "\n...[содержимое файла обрезано из-за размера]..."
            return content
    except Exception as e:
        return f"Не удалось прочитать файл {filename}: {str(e)}"

def control_system(action: str) -> str:
    """Управляет параметрами системы Windows.
    Доступные действия:
    - 'volume_up': сделать громче (+10%)
    - 'volume_down': сделать тише (-10%)
    - 'volume_mute': включить/выключить звук
    - 'media_play_pause': пауза/воспроизведение музыки или видео
    - 'media_next': следующий трек
    - 'media_prev': предыдущий трек
    - 'system_lock': заблокировать экран Windows
    - 'browser_back': вернуться назад в браузере (имитация Alt + Стрелка влево)
    - 'close_tab': закрыть активную вкладку (Ctrl + W)
    - 'next_tab': переключить на следующую вкладку (Ctrl + Tab)
    """
    print(f"[Управление системой]: {action}")
    if action == "volume_up":
        # 0xAF - VK_VOLUME_UP. Нажимаем 5 раз
        for _ in range(5):
            press_key(0xAF)
        return "Звук увеличен."
    elif action == "volume_down":
        # 0xAE - VK_VOLUME_DOWN. Нажимаем 5 раз
        for _ in range(5):
            press_key(0xAE)
        return "Звук уменьшен."
    elif action == "volume_mute":
        press_key(0xAD) # VK_VOLUME_MUTE
        return "Звук переключен (вкл/выкл)."
    elif action == "media_play_pause":
        press_key(0xB3) # VK_MEDIA_PLAY_PAUSE
        return "Медиа переведено в режим пауза/воспроизведение."
    elif action == "media_next":
        press_key(0xB5) # VK_MEDIA_NEXT_TRACK
        return "Переключено на следующий трек."
    elif action == "media_prev":
        press_key(0xB6) # VK_MEDIA_PREV_TRACK
        return "Переключено на предыдущий трек."
    elif action == "system_lock":
        try:
            ctypes.windll.user32.LockWorkStation()
            return "Экран компьютера заблокирован."
        except Exception as e:
            return f"Не удалось заблокировать экран: {str(e)}"
    elif action == "browser_back":
        # Alt + Стрелка влево (VK_MENU = 0x12, VK_LEFT = 0x25)
        press_keys([0x12, 0x25])
        return "Выполнен переход назад в браузере."
    elif action == "close_tab":
        # Ctrl + W (VK_CONTROL = 0x11, W = 0x57)
        press_keys([0x11, 0x57])
        return "Активная вкладка закрыта."
    elif action == "next_tab":
        # Ctrl + Tab (VK_CONTROL = 0x11, VK_TAB = 0x09)
        press_keys([0x11, 0x09])
        return "Переключено на следующую вкладку."
    else:
        return f"Неизвестное действие управления системой: {action}"

def analyze_screen(query: str) -> str:
    """Делает снимок текущего экрана пользователя, анализирует его с помощью зрения ИИ Gemini и отвечает на вопрос о содержимом экрана.
    Используй этот инструмент, когда пользователь просит посмотреть на экран, проанализировать картинку на мониторе, сказать что открыто и т.д.
    """
    print(f"[Зрение Джарвиса] Снимок экрана для запроса: {query}")
    try:
        # Делаем снимок всего экрана
        screenshot = ImageGrab.grab()
        
        # Сжимаем изображение согласно технической рекомендации (до 1024x1024 и JPEG с качеством 75%)
        resized_img = screenshot.resize((1024, 1024))
        
        # Сохраняем в буфер байтов как JPEG
        buffer = io.BytesIO()
        resized_img.save(buffer, format="JPEG", quality=75)
        img_bytes = buffer.getvalue()
        
        # Кодируем в base64
        base64_data = base64.b64encode(img_bytes).decode('utf-8')
        
        # Готовим запрос к Gemini
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            return "Ошибка: API-ключ Gemini не настроен."
            
        model_to_use = "gemini-2.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_to_use}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": f"Ты — зрение Джарвиса. Перед тобой снимок экрана создателя. Твоя задача: максимально точно и кратко ответить на запрос: '{query}'. Опиши только то, о чем спрашивают, будь предельно краток и лаконичен (1-2 предложения)."},
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": base64_data
                        }
                    }
                ]
            }]
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=25)
        if response.status_code == 200:
            res_json = response.json()
            try:
                text_result = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                return text_result
            except Exception as e:
                return f"Ошибка при разборе ответа ИИ: {e}"
        else:
            return f"Ошибка API зрения Gemini (код {response.status_code}): {response.text}"
            
    except Exception as e:
        return f"Не удалось проанализировать экран: {str(e)}"

def get_gemini_embedding(text: str) -> list:
    """Генерирует векторное представление (эмбеддинг) текста через Gemini API"""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY не установлен.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}"
    payload = {
        "model": "models/gemini-embedding-001",
        "content": {
            "parts": [{"text": text}]
        }
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()["embedding"]["values"]

def cosine_similarity(v1, v2):
    dot_product = sum(x * y for x, y in zip(v1, v2))
    norm_v1 = math.sqrt(sum(x * x for x in v1))
    norm_v2 = math.sqrt(sum(x * x for x in v2))
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

def save_memory(key: str, value: str) -> str:
    """Сохраняет важную информацию (воспоминание) о создателе, его предпочтениях, делах, друзьях или правилах в локальную долговременную память.
    Пример: key='любимый цвет', value='синий'
    """
    print(f"[Память Джарвиса] Сохранение воспоминания: {key} = {value}")
    try:
        memory_file = os.path.join(os.path.dirname(__file__), "memory.json")
        memories = []
        if os.path.exists(memory_file):
            try:
                with open(memory_file, "r", encoding="utf-8") as f:
                    memories = json.load(f)
            except Exception as e:
                print(f"Ошибка чтения memory.json: {e}")
                memories = []
                
        text_to_embed = f"{key}: {value}"
        try:
            embedding = get_gemini_embedding(text_to_embed)
        except Exception as e:
            print(f"Ошибка получения эмбеддинга при сохранении: {e}")
            embedding = []
            
        memories = [m for m in memories if m.get("key", "").lower() != key.lower()]
        
        memories.append({
            "key": key,
            "value": value,
            "text": text_to_embed,
            "embedding": embedding
        })
        
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(memories, f, ensure_ascii=False, indent=2)
            
        return f"Воспоминание '{key}: {value}' успешно записано в долговременную память, создатель."
    except Exception as e:
        return f"Не удалось записать воспоминание: {str(e)}"

def retrieve_memory_list(query: str, top_n: int = 5) -> list:
    """Ищет релевантные воспоминания в локальной памяти по векторному сходству и возвращает их списком"""
    try:
        memory_file = os.path.join(os.path.dirname(__file__), "memory.json")
        if not os.path.exists(memory_file):
            return []
            
        with open(memory_file, "r", encoding="utf-8") as f:
            memories = json.load(f)
            
        if not memories:
            return []
            
        try:
            query_emb = get_gemini_embedding(query)
        except Exception as e:
            print(f"Ошибка получения эмбеддинга при поиске: {e}")
            results = []
            for m in memories:
                score = 0.0
                words = query.lower().split()
                for w in words:
                    if w in m.get("key", "").lower() or w in m.get("value", "").lower():
                        score += 1.0
                if score > 0:
                    results.append((score, m))
            results.sort(key=lambda x: x[0], reverse=True)
            return [r[1] for r in results[:top_n]]
            
        scored_memories = []
        for m in memories:
            emb = m.get("embedding")
            if not emb:
                try:
                    emb = get_gemini_embedding(m["text"])
                    m["embedding"] = emb
                    with open(memory_file, "w", encoding="utf-8") as f:
                        json.dump(memories, f, ensure_ascii=False, indent=2)
                except:
                    continue
            
            sim = cosine_similarity(query_emb, emb)
            scored_memories.append((sim, m))
            
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        results = [m for sim, m in scored_memories if sim > 0.35]
        return results[:top_n]
        
    except Exception as e:
        print(f"Ошибка поиска в памяти: {e}")
        return []

def retrieve_memory(query: str) -> str:
    """Ищет информацию в долговременной памяти по семантическому сходству с запросом.
    Используй для ответов на вопросы о предпочтениях создателя, его друзьях, планах или прошлых разговорах.
    """
    print(f"[Память Джарвиса] Поиск в памяти по запросу: {query}")
    memories = retrieve_memory_list(query, top_n=3)
    if not memories:
        return "В памяти не найдено релевантных записей."
        
    result_str = "Найденные воспоминания:\n"
    for m in memories:
        result_str += f"- {m['key']}: {m['value']}\n"
    return result_str

from ctypes import wintypes
try:
    ctypes.windll.winmm.mciSendStringW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.UINT, wintypes.HANDLE]
    ctypes.windll.winmm.mciSendStringW.restype = wintypes.DWORD
    ctypes.windll.winmm.mciGetErrorStringW.argtypes = [wintypes.DWORD, wintypes.LPWSTR, wintypes.UINT]
    ctypes.windll.winmm.mciGetErrorStringW.restype = wintypes.BOOL
except Exception as e:
    print(f"[Ctypes Init Error for winmm MCI]: {e}")

def mci_send(command: str):
    buffer = ctypes.create_unicode_buffer(512)
    error = ctypes.windll.winmm.mciSendStringW(command, buffer, 512, 0)
    if error != 0:
        err_msg = ctypes.create_unicode_buffer(512)
        ctypes.windll.winmm.mciGetErrorStringW(error, err_msg, 512)
        print(f"[MCI Error for '{command}']: {err_msg.value}")
        return False, err_msg.value
    return True, buffer.value

def transliterate(text: str) -> str:
    cyrillic = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    latin = ['a','b','v','g','d','e','yo','zh','z','i','y','k','l','m','n','o','p','r','s','t','u','f','h','ts','ch','sh','shch','','y','','e','yu','ya']
    cyrillic_cap = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
    latin_cap = ['A','B','V','G','D','E','Yo','Zh','Z','I','Y','K','L','M','N','O','P','R','S','T','U','F','H','Ts','Ch','Sh','Shch','','Y','','E','Yu','Ya']
    
    tr = {}
    for c, l in zip(cyrillic, latin):
        tr[c] = l
    for c, l in zip(cyrillic_cap, latin_cap):
        tr[c] = l
        
    res = []
    for char in text:
        res.append(tr.get(char, char))
    return "".join(res)

def run_soundcloud_search(query: str) -> list:
    import re
    encoded = urllib.parse.quote(query)
    url = f"https://soundcloud.com/search?q={encoded}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        noscript_match = re.search(r'<noscript>(.*?)</noscript>', r.text, re.DOTALL)
        if not noscript_match:
            return []
        noscript_content = noscript_match.group(1)
        links = re.findall(r'href="([^"]*)"', noscript_content)
        tracks = []
        for l in links:
            if l.startswith('/') and l.count('/') == 2:
                parts = l.strip('/').split('/')
                if parts[0] not in ["pages", "terms", "privacy", "charts", "tags", "explore", "you", "discover", "stations", "settings", "search", "popular", "live", "imprint", "mobile", "news"]:
                    if parts[1] not in ["sounds", "sets", "people", "searches", "tracks", "playlists"]:
                        tracks.append("https://soundcloud.com" + l)
        return tracks
    except Exception as e:
        print(f"[SoundCloud Search Error]: {e}")
        return []

def autoplay_soundcloud_thread(url: str):
    import threading
    import time
    try:
        # Ждем загрузки вкладки в браузере
        time.sleep(4.5)
        # Имитируем нажатие клавиши Space (0x20) для автозапуска воспроизведения
        press_key(0x20)
        print("[Музыка Джарвиса] Отправлено нажатие Space для автозапуска.")
    except Exception as e:
        print(f"[Музыка Джарвиса] Ошибка автозапуска: {e}")

def play_music(query: str) -> str:
    """Ищет и автоматически запускает воспроизведение трека на SoundCloud в браузере по запросу пользователя.
    Используй для любых команд воспроизведения музыки или поиска песен (например, 'включи музыку', 'поставь песню Linkin Park', 'найди песню Зубарева').
    """
    import threading
    print(f"[Музыка Джарвиса] Открытие SoundCloud для запроса: {query}")
    try:
        # Ищем трек на SoundCloud
        tracks = run_soundcloud_search(query)
        if not tracks:
            # Пробуем транслитерацию, если ничего не найдено (актуально для русских запросов)
            translit_query = transliterate(query)
            if translit_query != query:
                print(f"[Музыка Джарвиса] Повторный поиск с транслитерацией: {translit_query}")
                tracks = run_soundcloud_search(translit_query)
                
        if tracks:
            track_url = tracks[0]
            print(f"[Музыка Джарвиса] Найден прямой трек: {track_url}")
            # Запускаем фоновый поток для симуляции нажатия Play/Space после загрузки
            threading.Thread(target=autoplay_soundcloud_thread, args=(track_url,), daemon=True).start()
            webbrowser.open(track_url)
            track_name = track_url.split('/')[-1].replace('-', ' ')
            return f"Запустил трек '{track_name}' на SoundCloud в браузере, создатель."
        else:
            # Если не нашли трек, открываем общую страницу поиска
            url = f"https://soundcloud.com/search?q={urllib.parse.quote(query)}"
            webbrowser.open(url)
            return f"Я не нашел прямого трека на SoundCloud, поэтому открыл страницу поиска по запросу '{query}', создатель."
    except Exception as e:
        return f"Не удалось воспроизвести музыку: {str(e)}"

def stop_music() -> str:
    """Останавливает/приостанавливает воспроизведение музыки в браузере с помощью медиа-клавиш."""
    print("[Музыка Джарвиса] Сигнал паузы/остановы медиа")
    press_key(0xB3) # VK_MEDIA_PLAY_PAUSE
    return "Сигнал приостановки музыки отправлен системе."

def pause_music() -> str:
    """Ставит воспроизведение музыки на паузу с помощью медиа-клавиш."""
    print("[Музыка Джарвиса] Сигнал паузы медиа")
    press_key(0xB3) # VK_MEDIA_PLAY_PAUSE
    return "Сигнал паузы отправлен системе."

def resume_music() -> str:
    """Возобновляет воспроизведение музыки с помощью медиа-клавиш."""
    print("[Музыка Джарвиса] Сигнал воспроизведения медиа")
    press_key(0xB3) # VK_MEDIA_PLAY_PAUSE
    return "Сигнал воспроизведения отправлен системе."

# --- Низкоуровневый ввод для игр (DirectInput) ---
import ctypes.wintypes
from ctypes import wintypes

SendInput = ctypes.windll.user32.SendInput

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.wintypes.WORD),
                ("wScan", ctypes.wintypes.WORD),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("time", ctypes.wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_ulong)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.wintypes.LONG),
                ("dy", ctypes.wintypes.LONG),
                ("mouseData", ctypes.wintypes.DWORD),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("time", ctypes.wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_ulong)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.wintypes.DWORD),
                ("ii", Input_I)]

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

def press_key_direct(hex_keycode):
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hex_keycode, KEYEVENTF_SCANCODE, 0, 0)
    x = Input(ctypes.c_ulong(1), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def release_key_direct(hex_keycode):
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hex_keycode, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, 0)
    x = Input(ctypes.c_ulong(1), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def move_mouse_relative(dx, dy):
    ii_ = Input_I()
    ii_.mi = MouseInput(dx, dy, 0, MOUSEEVENTF_MOVE, 0, 0)
    x = Input(ctypes.c_ulong(0), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def mouse_click(button="left"):
    ii_ = Input_I()
    flag_down = MOUSEEVENTF_LEFTDOWN if button == "left" else MOUSEEVENTF_RIGHTDOWN
    ii_.mi = MouseInput(0, 0, 0, flag_down, 0, 0)
    x = Input(ctypes.c_ulong(0), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
    time.sleep(0.05)
    flag_up = MOUSEEVENTF_LEFTUP if button == "left" else MOUSEEVENTF_RIGHTUP
    ii_.mi = MouseInput(0, 0, 0, flag_up, 0, 0)
    x = Input(ctypes.c_ulong(0), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def game_action(action: str, duration: float = 0.5) -> str:
    """Выполняет прямое игровое действие (движение WASD, прыжок, обзор, клики мыши) в игре (например, Майнкрафт).
    Параметры:
    - action: 'walk_forward' (идти вперед), 'walk_backward' (идти назад), 'walk_left' (идти влево), 'walk_right' (идти вправо), 
              'jump' (подпрыгнуть), 'crouch' (присесть), 'click_left' (ударить/сломать блок), 'click_right' (поставить блок/использовать), 
              'look_left' (повернуть камеру влево), 'look_right' (повернуть камеру вправо), 'look_up' (посмотреть вверх), 'look_down' (посмотреть вниз),
              'inventory' (открыть инвентарь), 'hit_repeatedly' (быстро кликать для боя)
    - duration: длительность удерживания кнопки движения в секундах (по умолчанию 0.5)
    """
    print(f"[Игровое действие]: {action} (длительность: {duration}с)")
    scan_codes = {
        "walk_forward": 0x11,  # W
        "walk_backward": 0x1F, # S
        "walk_left": 0x1E,     # A
        "walk_right": 0x20,    # D
        "jump": 0x39,          # Space
        "crouch": 0x2A,        # Shift
        "inventory": 0x12      # E
    }
    
    try:
        if action in ["walk_forward", "walk_backward", "walk_left", "walk_right", "crouch"]:
            code = scan_codes[action]
            press_key_direct(code)
            time.sleep(duration)
            release_key_direct(code)
            return f"Выполнено движение '{action}' в течение {duration} сек."
        elif action == "jump":
            code = scan_codes["jump"]
            press_key_direct(code)
            time.sleep(0.1)
            release_key_direct(code)
            return "Выполнен прыжок."
        elif action == "inventory":
            code = scan_codes["inventory"]
            press_key_direct(code)
            time.sleep(0.1)
            release_key_direct(code)
            return "Нажата клавиша инвентаря."
        elif action == "click_left":
            mouse_click("left")
            return "Выполнен клик левой кнопкой мыши."
        elif action == "click_right":
            mouse_click("right")
            return "Выполнен клик правой кнопкой мыши."
        elif action == "look_left":
            move_mouse_relative(-150, 0)
            return "Повернул камеру влево."
        elif action == "look_right":
            move_mouse_relative(150, 0)
            return "Повернул камеру вправо."
        elif action == "look_up":
            move_mouse_relative(0, -100)
            return "Посмотрел вверх."
        elif action == "look_down":
            move_mouse_relative(0, 100)
            return "Посмотрел вниз."
        elif action == "hit_repeatedly":
            for _ in range(5):
                mouse_click("left")
                time.sleep(0.15)
            return "Выполнена серия ударов мечом/кулаком."
        else:
            return f"Неизвестное игровое действие: {action}"
    except Exception as e:
        return f"Ошибка при выполнении игрового действия: {str(e)}"

def autonomous_play(goal: str, steps: int = 5) -> str:
    """Запускает цикл автономной игры Джарвиса. Джарвис делает скриншоты экрана, анализирует игровую ситуацию
    и сам принимает решения о поворотах, движении, прыжках и кликах в игре для достижения цели.
    Параметры:
    - goal: цель автономной игры (например, 'найди дерево и сруби его', 'беги за создателем', 'исследуй пещеру')
    - steps: количество циклов принятия решений (по умолчанию 5)
    """
    print(f"[Автономная игра] Старт цикла. Цель: '{goal}', шагов: {steps}")
    
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return "Ошибка: API-ключ Gemini не настроен."
        
    results = []
    
    for step in range(steps):
        print(f"[Автономная игра] Шаг {step + 1}/{steps}")
        
        # 1. Делаем снимок экрана
        try:
            screenshot = ImageGrab.grab()
            resized_img = screenshot.resize((1024, 1024))
            buffer = io.BytesIO()
            resized_img.save(buffer, format="JPEG", quality=75)
            img_bytes = buffer.getvalue()
            base64_data = base64.b64encode(img_bytes).decode('utf-8')
        except Exception as e:
            results.append(f"Шаг {step+1}: Не удалось сделать скриншот: {e}")
            continue
            
        # 2. Формируем запрос к модели для принятия решения
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + api_key
        headers = {"Content-Type": "application/json"}
        
        prompt = (
            f"Ты — автономный игровой ИИ-агент Джарвис. Твоя цель в игре (например, Rust, Minecraft): '{goal}'.\n"
            f"Перед тобой снимок текущего экрана игры.\n"
            f"Определи, что сейчас происходит на экране, и выбери 1-3 игровых действия для приближения к цели.\n"
            f"Ответь строго в формате JSON списка действий, например:\n"
            f"[\"look_left\", \"walk_forward 1.5\"]\n"
            f"Допустимые действия:\n"
            f"- \"walk_forward <seconds>\" (идти вперед, seconds от 0.1 до 3.0)\n"
            f"- \"walk_backward <seconds>\" (идти назад, seconds от 0.1 до 3.0)\n"
            f"- \"walk_left <seconds>\" (идти влево)\n"
            f"- \"walk_right <seconds>\" (идти вправо)\n"
            f"- \"jump\" (подпрыгнуть)\n"
            f"- \"crouch <seconds>\" (присесть)\n"
            f"- \"click_left\" (атаковать, выстрелить, ударить киянкой/инструментом или добыть ресурс)\n"
            f"- \"click_right\" (поставить постройку, прицелиться или использовать предмет)\n"
            f"- \"look_left\" (повернуть камеру влево)\n"
            f"- \"look_right\" (повернуть камеру вправо)\n"
            f"- \"look_up\" (посмотреть вверх)\n"
            f"- \"look_down\" (посмотреть вниз)\n"
            f"- \"hit_repeatedly\" (серия быстрых ударов/кликов)\n"
            f"- \"wait <seconds>\" (подождать)\n"
            f"Не пиши никакого другого текста, кроме JSON списка!"
        )
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": base64_data
                        }
                    }
                ]
            }],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            if response.status_code == 200:
                res_json = response.json()
                text_result = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                
                # Парсим JSON
                import json as py_json
                actions = py_json.loads(text_result)
                print(f"[Автономная игра] Решение модели: {actions}")
                
                step_log = []
                for act in actions:
                    act = act.strip()
                    parts = act.split()
                    if not parts:
                        continue
                    cmd = parts[0].strip('"').strip("'")
                    duration = 0.5
                    if len(parts) > 1:
                        try:
                            duration = float(parts[1])
                        except:
                            pass
                            
                    # Выполняем действие
                    res_act = game_action(cmd, duration)
                    step_log.append(f"{cmd}({duration}s) -> {res_act}")
                    time.sleep(0.15)
                    
                results.append(f"Шаг {step+1}: Выполнено: {', '.join(step_log)}")
                
            else:
                results.append(f"Шаг {step+1}: Ошибка модели: {response.text[:100]}")
        except Exception as e:
            results.append(f"Шаг {step+1}: Сбой: {e}")
            
        time.sleep(0.8) # Пауза перед следующим шагом
        
    return "Автономный игровой цикл завершен. Отчет по шагам:\n" + "\n".join(results)

# Словарь сопоставления функций для вызова по имени
AVAILABLE_TOOLS = {
    "run_terminal_command": run_terminal_command,
    "search_web": search_web,
    "open_website": open_website,
    "write_file": write_file,
    "read_file": read_file,
    "control_system": control_system,
    "analyze_screen": analyze_screen,
    "save_memory": save_memory,
    "retrieve_memory": retrieve_memory,
    "play_music": play_music,
    "stop_music": stop_music,
    "pause_music": pause_music,
    "resume_music": resume_music,
    "game_action": game_action,
    "autonomous_play": autonomous_play
}

# Описание инструментов для модели Gemini (API schema format)
GEMINI_TOOLS_DECLARATION = [
    {
        "name": "run_terminal_command",
        "description": "Запускает команду в PowerShell на компьютере пользователя и возвращает консольный вывод. Используй для работы с файловой системой, запуска скриптов, установки библиотек, проверки процессов и сетевых тестов.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "command": {
                    "type": "STRING",
                    "description": "Строка команды для выполнения в консоли Windows (PowerShell), например: 'python script.py' или 'dir'."
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "search_web",
        "description": "Ищет информацию в интернете (через DuckDuckGo) и возвращает краткие результаты. Используй для поиска новостей, погоды, фактов, курсов валют и ответов на вопросы, требующие актуальных данных.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Поисковый запрос на русском или английском языке."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "open_website",
        "description": "Открывает указанную веб-страницу (URL) в браузере пользователя по умолчанию. Используй, если пользователь просит открыть какой-то сайт (YouTube, ВКонтакте, Google, почту и т.д.).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "url": {
                    "type": "STRING",
                    "description": "Адрес сайта для открытия (например, 'https://youtube.com')."
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "write_file",
        "description": "Создает новый файл или перезаписывает существующий файл на диске компьютера пользователя. Используй для сохранения написанного программного кода, заметок, текстов или файлов конфигурации.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "filename": {
                    "type": "STRING",
                    "description": "Имя файла или относительный путь, например 'test_script.py' или 'note.txt'."
                },
                "content": {
                    "type": "STRING",
                    "description": "Полный текст, который нужно записать в создаваемый файл."
                }
            },
            "required": ["filename", "content"]
        }
    },
    {
        "name": "read_file",
        "description": "Читает содержимое указанного текстового файла с диска компьютера пользователя. Используй для анализа кода, логов, текстовых заметок.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "filename": {
                    "type": "STRING",
                    "description": "Имя или относительный путь к файлу для чтения."
                }
            },
            "required": ["filename"]
        }
    },
    {
        "name": "control_system",
        "description": "Управляет аппаратными функциями операционной системы Windows (громкость, воспроизведение медиа, блокировка экрана, навигация по вкладкам). Используй, когда пользователь просит сделать погромче, поставить на паузу, заблокировать компьютер и т.д.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "Действие для выполнения.",
                    "enum": [
                        "volume_up",
                        "volume_down",
                        "volume_mute",
                        "media_play_pause",
                        "media_next",
                        "media_prev",
                        "system_lock",
                        "browser_back",
                        "close_tab",
                        "next_tab"
                    ]
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "analyze_screen",
        "description": "Делает снимок текущего экрана создателя и отвечает на вопрос о содержимом экрана с помощью зрения ИИ.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Вопрос о содержимом экрана, например 'что там открыто?' или 'какая картинка на экране?'."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "save_memory",
        "description": "Сохраняет важный факт о пользователе (имя, предпочтения, любимые вещи, дела, правила) в локальную память для последующего использования.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "key": {
                    "type": "STRING",
                    "description": "Ключ (название факта), например 'любимый цвет', 'хобби', 'возраст'."
                },
                "value": {
                    "type": "STRING",
                    "description": "Значение факта для сохранения."
                }
            },
            "required": ["key", "value"]
        }
    },
    {
        "name": "retrieve_memory",
        "description": "Ищет релевантные факты и воспоминания в долговременной памяти по смысловому сходству с запросом.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Поисковый запрос для извлечения информации из памяти."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "play_music",
        "description": "Открывает поиск на SoundCloud в браузере по умолчанию по запросу пользователя.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Название песни или имя исполнителя для поиска."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "stop_music",
        "description": "Останавливает/приостанавливает воспроизведение музыки в браузере с помощью медиа-клавиш.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "pause_music",
        "description": "Ставит воспроизведение медиа в браузере на паузу с помощью медиа-клавиш.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "resume_music",
        "description": "Возобновляет воспроизведение медиа в браузере с помощью медиа-клавиш.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "game_action",
        "description": "Выполняет прямое игровое действие на клавиатуре или мыши в игре (Майнкрафт и др.) с использованием низкоуровневых скан-кодов. Позволяет ходить (WASD), прыгать, приседать, атаковать и крутить головой.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "Игровое действие для выполнения.",
                    "enum": [
                        "walk_forward",
                        "walk_backward",
                        "walk_left",
                        "walk_right",
                        "jump",
                        "crouch",
                        "click_left",
                        "click_right",
                        "look_left",
                        "look_right",
                        "look_up",
                        "look_down",
                        "inventory",
                        "hit_repeatedly"
                    ]
                },
                "duration": {
                    "type": "NUMBER",
                    "description": "Длительность нажатия клавиши движения в секундах (по умолчанию 0.5)."
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "autonomous_play",
        "description": "Запускает цикл автономной игры Джарвиса. Джарвис делает скриншоты экрана, анализирует игровую ситуацию и сам принимает решения о поворотах, движении, прыжках и кликах в игре для достижения цели (например, добежать до создателя, рубить дерево).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "goal": {
                    "type": "STRING",
                    "description": "Цель автономной игры, например 'руби дерево', 'беги за создателем', 'сражайся с зомби'."
                },
                "steps": {
                    "type": "INTEGER",
                    "description": "Количество шагов принятия решений (по умолчанию 5)."
                }
            },
            "required": ["goal"]
        }
    }
]
