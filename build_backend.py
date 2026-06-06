import os
import sys
import subprocess

def install_pyinstaller():
    """Устанавливает pyinstaller в виртуальное окружение, если его нет"""
    venv_pip = os.path.join("backend", ".venv", "Scripts", "pip.exe")
    if not os.path.exists(venv_pip):
        venv_pip = os.path.join("backend", ".venv", "bin", "pip")
        
    print("[Build Backend] Проверяем установку PyInstaller в виртуальном окружении...")
    try:
        # Проверяем, установлен ли pyinstaller
        subprocess.run([venv_pip, "show", "pyinstaller"], capture_output=True, check=True)
        print("[Build Backend] PyInstaller уже установлен.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[Build Backend] PyInstaller не найден в venv. Устанавливаем...")
        try:
            subprocess.run([venv_pip, "install", "pyinstaller"], check=True)
            print("[Build Backend] PyInstaller успешно установлен в виртуальное окружение.")
        except Exception as e:
            print(f"[Build Backend] Ошибка при установке PyInstaller: {e}")
            sys.exit(1)

def run_build():
    """Запускает компиляцию бэкенда через PyInstaller из виртуального окружения"""
    venv_pyinstaller = os.path.join("backend", ".venv", "Scripts", "pyinstaller.exe")
    if not os.path.exists(venv_pyinstaller):
        venv_pyinstaller = os.path.join("backend", ".venv", "bin", "pyinstaller")
        
    if not os.path.exists(venv_pyinstaller):
        print(f"[Build Backend] Ошибка: PyInstaller не найден по пути {venv_pyinstaller}!")
        sys.exit(1)
        
    print("[Build Backend] Запуск PyInstaller для сборки backend/server.py...")
    
    # Конструируем аргументы
    # Собираем все зависимости для faster_whisper, silero_vad, onnxruntime и edge_tts
    cmd = [
        venv_pyinstaller,
        "--onefile",
        "--name=jarvis_backend",
        "--collect-all=faster_whisper",
        "--collect-all=silero_vad",
        "--collect-all=onnxruntime",
        "--collect-all=edge_tts",
        "--hidden-import=pyaudio",
        "--hidden-import=torch",
        "--hidden-import=torchaudio",
        "--clean",
        "backend/server.py"
    ]
    
    print(f"[Build Backend] Команда сборки: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("[Build Backend] Сборка успешно завершена! Исполняемый файл находится в dist/jarvis_backend.exe")
    else:
        print(f"[Build Backend] Ошибка: Сборка завершилась неудачно (код возврата {result.returncode})")
        sys.exit(result.returncode)

if __name__ == "__main__":
    install_pyinstaller()
    run_build()
