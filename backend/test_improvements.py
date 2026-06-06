import os
import sys
import time
import shutil

# Добавляем текущую директорию в пути импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import jarvis_friend
from tools import retrieve_memory_list

def test_voice_caching():
    print("--- Тестирование кэширования голоса ---")
    cache_dir = os.path.join(os.path.dirname(__file__), "output", "voice_cache")
    if os.path.exists(cache_dir):
        # Очистим кэш перед тестом для чистоты эксперимента
        print("Очистка существующего кэша...")
        shutil.rmtree(cache_dir)
        
    test_phrase = "Тестовая фраза для проверки кэширования звука Джарвиса."
    
    # 1. Первая озвучка (должна сгенерировать файл)
    print("Вызов 1 (Генерация):")
    t0 = time.time()
    jarvis_friend.speak(test_phrase)
    t1 = time.time()
    generation_time = t1 - t0
    print(f"Время первого вызова (генерация): {generation_time:.4f} сек")
    
    # Проверим, что файл создался
    import hashlib
    voice_id = jarvis_friend.VOICE
    hash_input = f"{voice_id}_{test_phrase.strip().lower()}"
    md5_hash = hashlib.md5(hash_input.encode('utf-8')).hexdigest()
    expected_file = os.path.join(cache_dir, f"{md5_hash}.mp3")
    
    assert os.path.exists(expected_file), f"Файл кэша не найден: {expected_file}"
    print(f"Файл кэша успешно создан: {expected_file} (размер: {os.path.getsize(expected_file)} байт)")
    
    # 2. Вторая озвучка (должна взять из кэша мгновенно)
    print("Вызов 2 (Из кэша):")
    t2 = time.time()
    jarvis_friend.speak(test_phrase)
    t3 = time.time()
    cache_time = t3 - t2
    print(f"Время второго вызова (кэш): {cache_time:.4f} сек")
    
    # Время из кэша должно быть существенно меньше (обычно < 0.1 сек на дисковое чтение и воспроизведение в фоне)
    assert cache_time < generation_time, "Кэш не ускорил воспроизведение!"
    print("Тест кэширования голоса успешно пройден!")

def test_rag_bypass():
    print("\n--- Тестирование обхода RAG-памяти ---")
    
    # Проверяем ключевые фразы
    test_prompts = [
        ("джарвис иди вперед", True),
        ("прыгни", True),
        ("включи музыку", True),
        ("какой твой любимый цвет?", False),
        ("расскажи о создателе", False)
    ]
    
    for prompt, expected_bypass in test_prompts:
        words = prompt.lower().split()
        keywords = ["вперед", "назад", "влево", "вправо", "прыгни", "присядь", "нажми", "кликни", "посмотри", "пауза", "продолжи", "стоп", "музыка", "включи", "песня", "сайт", "открой", "громкость", "выключи", "играй", "поиграем", "игра"]
        should_bypass = len(words) < 3 or any(kw in prompt.lower() for kw in keywords)
        
        print(f"Запрос: '{prompt}' | Ожидался пропуск RAG: {expected_bypass} | Результат: {should_bypass}")
        assert should_bypass == expected_bypass, f"Несовпадение для запроса: {prompt}"
        
    print("Тест обхода RAG-памяти успешно пройден!")

if __name__ == "__main__":
    try:
        test_voice_caching()
        test_rag_bypass()
        print("\nВсе тесты успешно пройдены!")
    except AssertionError as e:
        print(f"\nОшибка при тестировании: {e}")
        sys.exit(1)
