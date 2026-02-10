import io
try:
    from gtts import gTTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

def generate_voice(text, lang='ru'):
    if not TTS_AVAILABLE:
        print("TTS not available")
        return None
    try:
        tts = gTTS(text, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        print("Voice generated successfully")
        return fp
    except Exception as e:
        print(f"Error generating voice: {e}")
        return None

def main():
    if TTS_AVAILABLE:
        fp = generate_voice("Привет, это тест голоса.")
        if fp:
            print("TTS works")
        else:
            print("TTS failed")
    else:
        print("TTS not available")

main()