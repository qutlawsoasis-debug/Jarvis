import os, subprocess, winsound

FFMPEG = os.path.abspath("backend/.venv/Scripts/ffmpeg.exe")
clips = [
    ("speakers/tmp/board20031_1.mp3", "speakers/tmp/play1.wav"),
    ("speakers/tmp/board20031_2.mp3", "speakers/tmp/play2.wav"),
]

for mp3, wav in clips:
    subprocess.run([FFMPEG, '-i', mp3, '-ar', '22050', '-ac', '1', '-t', '10', '-y', wav], capture_output=True)
    print(f"Воспроизвожу {mp3} ...")
    winsound.PlaySound(os.path.abspath(wav), winsound.SND_FILENAME)
    print("Следующий...")

print("Все клипы прослушаны!")
