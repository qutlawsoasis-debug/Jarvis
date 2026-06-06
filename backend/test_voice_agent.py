import os
import sys
import json
from dotenv import load_dotenv

# Добавляем пути
sys.path.append(os.path.dirname(__file__))

from jarvis_friend import process_ai_interaction, chat_history, GEMINI_API_KEY
from tools import run_terminal_command

# Загружаем переменные окружения
load_dotenv()

def run_test():
    print("==================================================")
    print("     ТЕСТИРОВАНИЕ БЭКЕНДА ДЖАРВИСА БЕЗ МИКРОФОНА  ")
    print("==================================================")
    
    if not GEMINI_API_KEY:
        print("[ОШИБКА]: GEMINI_API_KEY не установлен в файле .env!")
        return
        
    print(f"API Ключ загружен: {GEMINI_API_KEY[:6]}...{GEMINI_API_KEY[-4:] if len(GEMINI_API_KEY) > 10 else ''}")
    
    # Тест 1: Простая беседа
    print("\n--- ТЕСТ 1: Простая беседа (Ожидается дружеский голосовой ответ) ---")
    test_prompt = "Привет, друг! Как твои дела сегодня?"
    print(f"Запрос пользователя: '{test_prompt}'")
    process_ai_interaction(test_prompt)
    
    # Тест 2: Вызов инструмента (поиск информации)
    print("\n--- ТЕСТ 2: Вызов инструмента поиска (Ожидается обращение к DuckDuckGo и ответ) ---")
    test_prompt_2 = "Джарвис, погугли, какая столица Франции."
    print(f"Запрос пользователя: '{test_prompt_2}'")
    process_ai_interaction(test_prompt_2)
    
    # Тест 3: Вызов инструмента управления файлами
    print("\n--- ТЕСТ 3: Вызов инструмента создания файла (Ожидается создание test.txt) ---")
    test_prompt_3 = "Джарвис, создай текстовый файл с именем test_jarvis.txt и запиши туда текст 'Привет от Джарвиса!'"
    print(f"Запрос пользователя: '{test_prompt_3}'")
    process_ai_interaction(test_prompt_3)
    
    # Проверяем, создался ли файл
    if os.path.exists("test_jarvis.txt"):
        print("[УСПЕХ]: Файл test_jarvis.txt был успешно создан!")
        # Удаляем тестовый файл
        try:
            os.remove("test_jarvis.txt")
            print("Тестовый файл test_jarvis.txt удален.")
        except Exception as e:
            print(f"Не удалось удалить тестовый файл: {e}")
    else:
        print("[ОШИБКА]: Тестовый файл не был создан!")

    print("\n==================================================")
    print("              ТЕСТИРОВАНИЕ ЗАВЕРШЕНО              ")
    print("==================================================")

if __name__ == "__main__":
    run_test()
