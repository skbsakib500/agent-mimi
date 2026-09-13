"""Text-to-speech for Mimi."""
import subprocess, shutil

def available():
    return shutil.which("termux-tts-speak") is not None

def speak(text, lang="bn", rate=1.0, pitch=1.0, engine=None):
    if not available():
        return False
    cmd = ["termux-tts-speak", "-l", lang, "-r", str(rate), "-p", str(pitch)]
    if engine:
        cmd += ["-e", engine]
    cmd.append(str(text)[:500])
    try:
        subprocess.Popen(cmd,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def en(text):
    return speak(text, lang="en")

def bn(text):
    return speak(text, lang="bn")

def main():
    from .ui import BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW
    from .ui import c, clear, header, pause
    clear()
    header("🔊 TEXT-TO-SPEECH", "Termux TTS")
    if not available():
        print(c("\n  termux-tts-speak not found.", RED))
        print("  Run: pkg install -y termux-api")
        pause(); return
    print(c("\n  TTS is available.", GREEN))
    print()
    print("  1. Test (Bangla)")
    print("  2. Test (English)")
    print("  3. Custom text")
    print("  0. Back")
    ch = input(c("\n  > Select: ")).strip()
    if ch == "1":
        bn("হ্যালো, আমি মিমি, আপনার ব্যক্তিগত সহকারী")
        print(c("  Spoken.", GREEN))
    elif ch == "2":
        en("Hello, I am Mimi, your personal assistant")
        print(c("  Spoken.", GREEN))
    elif ch == "3":
        t = input("  Text: ").strip()
        if t:
            lang = input("  Lang [bn]: ").strip() or "bn"
            speak(t, lang=lang)
    elif ch == "0":
        return
    pause()

run = main
