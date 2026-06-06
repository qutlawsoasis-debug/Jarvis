import asyncio
import sys
import edge_tts
import winsound
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

test_text = "Привет, Мирон! Я твой голосовой ассистент Джарвис. Этот голос абсолютно бесплатный, работает без интернета и лимитов, звучит чисто и понятно. Как тебе такой вариант?"

async def test_voice(voice_id, filename):
    print(f"\n🎙️ Синтезирую через Edge-TTS: {voice_id}...")
    communicate = edge_tts.Communicate(test_text, voice_id, rate="+10%")
    await communicate.save(filename)
    
    print("   Воспроизвожу...")
    # Для MP3 используем PowerShell
    import subprocess
    abs_path = os.path.abspath(filename)
    subprocess.run(
        ['powershell', '-Command',
         f'$p = New-Object System.Windows.Media.MediaPlayer; $p.Open([uri]"{abs_path}"); $p.Play(); Start-Sleep -Seconds 7; $p.Stop()'],
        timeout=12, capture_output=True
    )
    print("   Готово!")

async def main():
    # 1. Дмитрий
    await test_voice("ru-RU-DmitryNeural", "test_edge_dmitry.mp3")
    # 2. Сергей
    await test_voice("ru-RU-SergeiNeural", "test_edge_sergei.mp3")

if __name__ == "__main__":
    asyncio.run(main())
