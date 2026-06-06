import os
import sys
import subprocess

# Configure UTF-8 encoding for standard output/error
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def get_pip_cmd():
    """Detects pip command: virtual environment pip has priority, fallbacks to sys.executable -m pip"""
    venv_pip = os.path.join("backend", ".venv", "Scripts", "pip.exe")
    if os.path.exists(venv_pip):
        return [venv_pip]
        
    venv_pip_bin = os.path.join("backend", ".venv", "bin", "pip")
    if os.path.exists(venv_pip_bin):
        return [venv_pip_bin]
        
    return [sys.executable, "-m", "pip"]

def get_pyinstaller_cmd():
    """Detects pyinstaller command: virtual environment pyinstaller has priority, fallbacks to global/python modules"""
    venv_pyinstaller = os.path.join("backend", ".venv", "Scripts", "pyinstaller.exe")
    if os.path.exists(venv_pyinstaller):
        return [venv_pyinstaller]
        
    venv_pyinstaller_bin = os.path.join("backend", ".venv", "bin", "pyinstaller")
    if os.path.exists(venv_pyinstaller_bin):
        return [venv_pyinstaller_bin]
        
    # Check if pyinstaller is in PATH
    try:
        subprocess.run(["pyinstaller", "--version"], capture_output=True, check=True)
        return ["pyinstaller"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
        
    # Check if PyInstaller can be run via python module
    try:
        subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], capture_output=True, check=True)
        return [sys.executable, "-m", "PyInstaller"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
        
    return None

def install_pyinstaller():
    """Installs pyinstaller if not present in the detected environment"""
    pip_cmd = get_pip_cmd()
    pyinstaller_cmd = get_pyinstaller_cmd()
    
    if pyinstaller_cmd is not None:
        print(f"[Build Backend] PyInstaller is already available via: {' '.join(pyinstaller_cmd)}")
        return

    print("[Build Backend] PyInstaller not found. Installing via pip...")
    try:
        subprocess.run(pip_cmd + ["install", "pyinstaller"], check=True)
        print("[Build Backend] PyInstaller installed successfully.")
    except Exception as e:
        print(f"[Build Backend] Error installing PyInstaller: {e}")
        sys.exit(1)

def run_build():
    """Runs backend compilation using PyInstaller"""
    pyinstaller_cmd = get_pyinstaller_cmd()
    if pyinstaller_cmd is None:
        print("[Build Backend] Error: PyInstaller is still not available after installation step!")
        sys.exit(1)
        
    print(f"[Build Backend] Running PyInstaller via: {' '.join(pyinstaller_cmd)}")
    
    # Construct PyInstaller arguments
    cmd = pyinstaller_cmd + [
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
    
    print(f"[Build Backend] Build command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("[Build Backend] Build completed successfully! Executable is at dist/jarvis_backend.exe")
    else:
        print(f"[Build Backend] Error: Build failed with return code {result.returncode}")
        sys.exit(result.returncode)

if __name__ == "__main__":
    install_pyinstaller()
    run_build()
