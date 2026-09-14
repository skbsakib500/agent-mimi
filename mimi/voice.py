"""Voice command - speech to text."""
import subprocess, shutil, json

def available():
    return shutil.which("termux-speech-to-text") is not None

def listen(timeout=15):
    if not available():
        return None
    try:
        result = subprocess.run(
            ["termux-speech-to-text"],
            capture_output=True, text=True, timeout=timeout)
        text = (result.stdout or "").strip()
        if not text:
            return None
        if text.startswith("["):
            try:
                arr = json.loads(text)
                text = " ".join(arr) if isinstance(arr, list) else text
            except Exception:
                pass
        return text.strip()
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None

def main():
    from .ui import BOLD, CYAN, DIM, GREEN, RED, YELLOW
    from .ui import c, clear, header, pause
    clear()
    header("🎤 VOICE", "Speak to Mimi")
    if not available():
        print(c("\n  termux-speech-to-text not found.", RED))
        print("  Install: pkg install -y termux-api")
        print("  And Termux:API app from F-Droid.")
        pause()
        return
    print(c("\n  🎤 Listening... speak now.", YELLOW + BOLD))
    text = listen()
    if not text:
        print(c("  (nothing heard)", RED))
        pause()
        return
    print(c(f"\n  You said: {text}", CYAN))
    from .agent import Agent
    agent = Agent()
    reply = agent.respond(text)
    print()
    for ln in reply.splitlines():
        print(c(f"  Mimi: {ln}", GREEN))
    try:
        from . import speak
        if speak.available():
            speak.speak(reply, lang="bn")
    except Exception:
        pass
    pause()

run = main
