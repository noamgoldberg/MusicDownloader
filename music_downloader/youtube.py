from typing import Dict
import os
import datetime
import zipfile
from io import BytesIO
from typing import List
import yt_dlp

from music_downloader.base import BaseSong


class YouTubeSong(BaseSong):
    
    def __init__(self, url: str):
        super().__init__(url)

    def get_platform(self) -> str:
        return "YouTube"

    @staticmethod
    def is_url_valid(url: str) -> bool:
        return "youtube.com/watch?" in url

    def scrape_song_info(self) -> Dict[str, str]:
        ydl_opts = {"quiet": True, "extract_flat": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=False)
        title = info.pop("title")
        if ' - ' not in title:
            title = f"{title} by {self.artist}"
        info["song"] = title
        info["artist"] = info.pop("uploader")
        info["embed_url"] = f"https://www.youtube.com/embed/{info.pop('id')}"
        return info

    def _download_audio(self, verbose: int = 0):
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
        self.song_urls = self._get_playlist_songs()
        self._songs = None
        self.filename = "playlist.zip"
        self.audio_zipped = None
        self.audio = None
        self.entity_type = "playlist"
        self.platform = "YouTube"
        self.download_from = "YouTube"

    @staticmethod
    def is_url_valid(url: str) -> bool:
        return "youtube.com/playlist?" in url

    def _get_playlist_songs(self) -> List[str]:
        ydl_opts = {"quiet": True, "extract_flat": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=False)
        return [entry['url'] for entry in info.get('entries', [])]

    @property
    def songs(self) -> List[YouTubeSong]:
        if self._songs is None:
            self._songs = [YouTubeSong(url) for url in self.song_urls]
        return self._songs

    def download_audio(self, verbose: int = 0):
        if self.audio is None:
            self.audio = [song.download_audio(verbose=verbose) for song in self.songs]
        return self.audio

    def zip_audio(self) -> BytesIO:
        self.download_audio()  # Ensure all audio is downloaded first
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for song in self.songs:
                audio_data = song.audio.getvalue()  # Directly get the audio data in memory
                zip_file.writestr(song.filename.replace('_', ' '), audio_data)
        zip_buffer.seek(0)  # Ensure the memory pointer is at the beginning before returning
        self.audio_zipped = zip_buffer
        return self.audio_zipped