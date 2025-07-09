import os
from gtts import gTTS

def text_to_speech_file(text: str, folder: str) -> str:
    # Create the output directory if it doesn't exist
    output_dir = os.path.join("user_upload", folder)
    os.makedirs(output_dir, exist_ok=True)

    # Define the save path
    save_file_path = os.path.join(output_dir, "audio.mp3")

    # Generate TTS audio using gTTS
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(save_file_path)

    print(f"{save_file_path}: A new audio file was saved successfully!")

    # Return the path of the saved audio file
    return save_file_path

# Example usage
# text_to_speech_file("Hello, this is a test of Google Text-to-Speech.", "b60f641e-5b4f-11f0-88b9-7429af1d0a80")
