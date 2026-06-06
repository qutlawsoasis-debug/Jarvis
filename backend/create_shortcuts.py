import os
import subprocess

def create_shortcuts():
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_path = os.path.join(current_dir, "run_jarvis.vbs")
    bat_target_path = os.path.join(current_dir, "run_jarvis.bat")
    
    # PowerShell скрипт для создания ярлыков
    ps_script = f"""
    $WshShell = New-Object -ComObject WScript.Shell
    
    # Ярлык на Рабочем столе (запускает .bat напрямую для видимости консоли)
    $DesktopPath = [System.IO.Path]::Combine($env:USERPROFILE, "Desktop", "Jarvis.lnk")
    $Shortcut = $WshShell.CreateShortcut($DesktopPath)
    $Shortcut.TargetPath = "{bat_target_path}"
    $Shortcut.WorkingDirectory = "{current_dir}"
    $Shortcut.IconLocation = "shell32.dll,138"  # Иконка микрофона
    $Shortcut.Save()
    Write-Output "Shortcut created on Desktop: $DesktopPath"
    
    # Ярлык в автозагрузке
    $StartupPath = [System.IO.Path]::Combine($env:APPDATA, "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "Jarvis.lnk")
    $StartupShortcut = $WshShell.CreateShortcut($StartupPath)
    $StartupShortcut.TargetPath = "{target_path}"
    $StartupShortcut.WorkingDirectory = "{current_dir}"
    $StartupShortcut.Save()
    Write-Output "Startup shortcut created: $StartupPath"
    """
    
    # Запуск PowerShell
    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    except Exception as e:
        print("Failed to run PowerShell script:", e)

if __name__ == "__main__":
    create_shortcuts()
