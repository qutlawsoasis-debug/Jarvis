import os, subprocess

filename = os.path.abspath('test_output.wav')
print(f'Воспроизвожу: {filename}')
print(f'Размер: {os.path.getsize(filename)} байт')

# Метод 1: winsound (только PCM WAV)
try:
    import winsound
    winsound.PlaySound(filename, winsound.SND_FILENAME)
    print('winsound OK!')
except Exception as e:
    print(f'winsound ошибка: {e}')

# Метод 2: PowerShell через subprocess
try:
    cmd = f'(New-Object Media.SoundPlayer "{filename}").PlaySync()'
    result = subprocess.run(['powershell', '-Command', cmd], timeout=30, capture_output=True, text=True)
    if result.returncode == 0:
        print('PowerShell SoundPlayer OK!')
    else:
        print(f'PowerShell ошибка: {result.stderr}')
except Exception as e:
    print(f'subprocess ошибка: {e}')
