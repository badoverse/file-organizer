from pathlib import Path
import os
import shutil
import subprocess


imgExtensions = [
    ".png",
    ".jpeg",
    ".jpg",
    ".webp",
    ".gif",
]

videoExtensions = [
    ".mp4",
    ".webm",
]

audioExtensions = [
    ".mp3",
    ".wav",
]

exeExtensions = [
    ".exe",
]

fileExtensions = imgExtensions + videoExtensions + audioExtensions + exeExtensions


home = Path.home()

source_dir = home / "Downloads" # where you want your file to be extracted from

destination_dir = Path(
    subprocess.check_output(
        [
            "powershell",
            "-Command",
            "[Environment]::GetFolderPath('MyDocuments')" # replace with your destination folder
        ]
    )
    .decode()
    .strip()
)


extensionFolder = {
    "imgs": destination_dir / "imgs",
    "videos": destination_dir / "videos",
    "audios": destination_dir / "audios",
    "executables": destination_dir / "executables",
}


def organize(folder):
    print("Scanning:", folder)

    for root, dirs, files in os.walk(folder):
        for file in files:
            filepath = Path(root) / file
            extension = filepath.suffix.lower()


            if extension in fileExtensions:
                move_file(filepath, extension)


def move_file(filepath, extension):

    if extension in imgExtensions:
        destination = extensionFolder["imgs"]

    elif extension in videoExtensions:
        destination = extensionFolder["videos"]

    elif extension in audioExtensions:
        destination = extensionFolder["audios"]

    elif extension in exeExtensions:
        destination = extensionFolder["executables"]

    else:
        return

    print(f"Moving: {filepath} -> {destination}")

    shutil.move(filepath, destination)


organize(source_dir)