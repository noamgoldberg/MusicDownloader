from typing import Dict, Union
import os
import datetime
import zipfile
from io import BytesIO
from typing import List
import yt_dlp

from music_downloader.base import BaseSong, BasePlaylist


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
        info["artist"] = info.pop("uploader")
        title = info.pop("title")
        if ' - ' not in title:
            title = f"{title} by {info['artist']}"
        info["song"] = title
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


class YouTubePlaylist(BasePlaylist):
    
    def __init__(self, url: str):
        super().__init__(url)
    
    def get_platform(self) -> str:
        return "YouTube"

    @staticmethod
    def is_url_valid(url: str) -> bool:
        return "youtube.com/playlist?" in url
    
    def _get_playlist_songs(self) -> List[str]:
        ydl_opts = {"quiet": True, "extract_flat": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=False)
        return [entry['url'] for entry in info.get('entries', [])]

    def scrape_playlist_info(self) -> Dict[str, Union[str, List[str]]]:
        ydl_opts = {"quiet": True, "extract_flat": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=False)
        info["title"] = info.get("title", "Unknown Title")
        info["curator"] = info.pop("uploader", "Unknown Curator")
        info["song_urls"] = [s['url'] for s in info.get('entries', [])]
        info["embed_url"] = f"https://www.youtube.com/embed/{info.get('id')}" if info.get("id") else None
        return info

    def create_song(self, url: str):
        return YouTubeSong(url)
    
    @property
    def thumbnail(self) -> str:
        return self.info.get("thumbnail")
