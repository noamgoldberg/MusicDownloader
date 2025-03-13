import tempfile
import os
import hashlib
import datetime
import zipfile
from io import BytesIO
from typing import List, Optional
from pathlib import Path


import yt_dlp

class YouTubeVideo:
    
    ENTITY_TYPE = "song"
    
    def __init__(self, url: str):
        self.url = url
        self.info = self._get_video_info()
        self.artist = self.info.get('uploader', 'Unknown Artist')
        self._title = self._format_song_title(self.info.get('title', 'Unknown Title'))
        self.entity_type = "song"
        self.platform = "YouTube"
        self.download_from = "YouTube"
        self._audio = None

    @staticmethod
    def is_url_valid(url: str) -> bool:
        return "youtube.com/watch?" in url

    def _get_video_info(self):
        ydl_opts = {"quiet": True, "extract_flat": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(self.url, download=False)

    def _format_song_title(self, title: str) -> str:
        if ' - ' not in title:
            title += f" by {self.artist}"
        return title

    @property
    def title(self) -> str:
        return self._title

    @property
    def embed_url(self) -> str:
        return f"https://www.youtube.com/embed/{self.info.get('id', '')}"

    @property
    def filename(self) -> str:
        return f"{self._title}.mp3"

    @property
    def audio(self) -> BytesIO:
        """Returns the cached audio if already downloaded, otherwise downloads it."""
        if self._audio is None:
            self.download_audio()
        return self._audio

    @audio.setter
    def audio(self, buffer: BytesIO):
        """Validates and sets the audio buffer."""
        if not isinstance(buffer, BytesIO):
            raise TypeError(f"Invalid type for 'audio' property; expected BytesIO, got {type(buffer).__name__}")
        self._audio = buffer

    def download_audio(self, verbose: int = 0):
        """Downloads the audio and caches it in the _audio attribute."""
        if self._audio is None:
            if verbose >= 1:
                print(f"...Downloading audio for '{self.title}': {self.url}")

            # Create a temporary file with a controlled output format
            temp_file_dir = "data"
            os.makedirs(temp_file_dir, exist_ok=True)
            current_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            temp_filename, suffix = f"{temp_file_dir}/{current_time}", ".mp3"
            temp_filepath = f"{temp_filename}{suffix}"
            ydl_opts = {
                'format': 'bestaudio',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                # 'postprocessor_args': ['-ar', '44100'],  # Ensures a standard sample rate
                'outtmpl': temp_filename,  # Save to a temporary file
                'quiet': verbose == 0,
                # 'no_warnings': True,
                # 'extractaudio': True,  # Explicitly ask for audio extraction
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])

            # Read the file into memory
            with open(temp_filepath, 'rb') as f:  # yt_dlp appends .mp3 after processing
                self._audio = BytesIO(f.read())

            # Clean up the temporary file
            os.remove(temp_filepath)

        return self._audio


class YouTubePlaylist:

    ENTITY_TYPE = "playlist"

    def __init__(self, url: str):
        self.url = url
        self.video_urls = self._get_playlist_videos()
        self._videos = None
        self.filename = "playlist.zip"
        self.audio_zipped = None
        self.audio = None
        self.entity_type = "playlist"
        self.platform = "YouTube"
        self.download_from = "YouTube"

    @staticmethod
    def is_url_valid(url: str) -> bool:
        return "youtube.com/playlist?" in url

    def _get_playlist_videos(self) -> List[str]:
        ydl_opts = {"quiet": True, "extract_flat": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=False)
        return [entry['url'] for entry in info.get('entries', [])]

    @property
    def videos(self) -> List[YouTubeVideo]:
        if self._videos is None:
            self._videos = [YouTubeVideo(url) for url in self.video_urls]
        return self._videos

    def download_audio(self, verbose: int = 0):
        if self.audio is None:
            self.audio = [video.download_audio(verbose=verbose) for video in self.videos]
        return self.audio

    def zip_audio(self) -> BytesIO:
        self.download_audio()  # Ensure all audio is downloaded first
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for video in self.videos:
                audio_data = video.audio.getvalue()  # Directly get the audio data in memory
                zip_file.writestr(video.filename.replace('_', ' '), audio_data)
        zip_buffer.seek(0)  # Ensure the memory pointer is at the beginning before returning
        self.audio_zipped = zip_buffer
        return self.audio_zipped