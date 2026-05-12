from pathlib import Path

from gtts import gTTS

def text_to_speech_file(text: str, output_path: str | Path) -> str:
    save_file_path = Path(output_path)
    save_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate TTS audio using gTTS
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(str(save_file_path))

    print(f"{save_file_path}: A new audio file was saved successfully!")

    # Return the path of the saved audio file
    return str(save_file_path)

# Example usage
# text_to_speech_file("Hello, this is a test of Google Text-to-Speech.", "b60f641e-5b4f-11f0-88b9-7429af1d0a80")
