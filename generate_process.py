import os
from reel import text_to_speech_file
import time
import subprocess

def text_to_audio(folder):
    print("TTA-- ",folder)
    with open(f"user_upload/{folder}/description.txt") as f:
        text = f.read()
    print( text,folder)
    text_to_speech_file(text,folder)

def create_reel(folder):
    command = f'''ffmpeg -f concat -safe 0 -i user_upload/{folder}/input.txt -i user_upload/{folder}/audio.mp3 -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black" -c:v libx264 -c:a aac -shortest -r 30 -pix_fmt yuv420p static/reel/{folder}.mp4'''
    subprocess.run(command,shell=True, check=True)
    print("CR-- ",folder)

if __name__ == "__main__":
    while True:
        print("processing...")
        with open("done.txt", "r") as f:
            done_folders = f.readlines()
        done_folders = [s.strip() for s in done_folders]  # Clean up newline characters
        folders = os.listdir("user_upload")
        for folder in folders:
            if(folder not in done_folders):
                # folder = "588...."
                text_to_audio(folder)
                create_reel(folder)
                print("Process generation completed.")
                with open("done.txt", "a") as f:
                    f.write(folder + "\n")
        time.sleep(3)