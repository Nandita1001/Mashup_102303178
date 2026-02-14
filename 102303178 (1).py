import sys
import os
import yt_dlp
from pydub import AudioSegment

def download_videos(singer, num_videos):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True
    }

    os.makedirs("downloads", exist_ok=True)

    search_query = f"ytsearch{num_videos}:{singer} songs"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([search_query])


def convert_and_trim(duration):
    trimmed_files = []
    os.makedirs("trimmed", exist_ok=True)

    for file in os.listdir("downloads"):
        if file.endswith(".webm") or file.endswith(".m4a"):
            input_path = os.path.join("downloads", file)
            audio = AudioSegment.from_file(input_path)
            trimmed_audio = audio[:duration * 1000]
            output_path = os.path.join("trimmed", file.split('.')[0] + ".mp3")
            trimmed_audio.export(output_path, format="mp3")
            trimmed_files.append(output_path)

    return trimmed_files


def merge_audios(files, output_name):
    combined = AudioSegment.empty()
    for file in files:
        audio = AudioSegment.from_mp3(file)
        combined += audio

    combined.export(output_name, format="mp3")


def main():
    if len(sys.argv) != 5:
        print("Usage: python <program.py> <SingerName> <NumberOfVideos> <AudioDuration> <OutputFileName>")
        sys.exit(1)

    singer = sys.argv[1]
    try:
        num_videos = int(sys.argv[2])
        duration = int(sys.argv[3])
    except ValueError:
        print("NumberOfVideos and AudioDuration must be integers.")
        sys.exit(1)

    output_file = sys.argv[4]

    if num_videos <= 10:
        print("NumberOfVideos must be greater than 10.")
        sys.exit(1)

    if duration <= 20:
        print("AudioDuration must be greater than 20 seconds.")
        sys.exit(1)

    try:
        print("Downloading videos...")
        download_videos(singer, num_videos)

        print("Converting and trimming...")
        trimmed_files = convert_and_trim(duration)

        print("Merging audios...")
        merge_audios(trimmed_files, output_file)

        print(f"Success! Output saved as {output_file}")

    except Exception as e:
        print("An error occurred:", e)


if __name__ == "__main__":
    main()
