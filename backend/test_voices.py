"""Тест разных голосов Edge-TTS — сравниваем варианты для Джарвиса"""
import asyncio
import edge_tts
import winsound
import os

test_text = "Системы инициализированы. Я на связи, сэр Мирон. Чем могу помочь?"

voices = [
    ("ru-RU-DmitryNeural", "Дмитрий (мужской, стандартный)"),
    ("ru-RU-SergeiNeural", "Сергей (мужской, чёткий)"),
    ("en-GB-RyanNeural", "Ryan British (английский, ближе к Джарвису)"),
    ("en-GB-ThomasNeural", "Thomas British (английский, спокойный)"),
]

async def test_voice(voice_id, label):
    filename = f"voice_test_{voice_id}.mp3"
    print(f"\n🎙️ Тестирую: {label} [{voice_id}]")
    try:
        comm = edge_tts.Communicate(test_text, voice_id, rate="+10%")
        await comm.save(filename)
        print(f"   Воспроизвожу...")
        # Для MP3 используем PowerShell
        import subprocess
        abs_path = os.path.abspath(filename)
        subprocess.run(
            ['powershell', '-Command',
             f'$p = New-Object System.Windows.Media.MediaPlayer; $p.Open([uri]"{abs_path}"); $p.Play(); Start-Sleep -Seconds 6; $p.Stop()'],
            timeout=10, capture_output=True
        )
        print(f"   ✓ Готово")
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")

async def main():
    for voice_id, label in voices:
        await test_voice(voice_id, label)
        await asyncio.sleep(1)

asyncio.run(main())
