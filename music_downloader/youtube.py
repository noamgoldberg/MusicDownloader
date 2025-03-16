from typing import Dict, Union, Any
import os
from io import BytesIO
from typing import List
import yt_dlp
from pytube import YouTube, Playlist
import datetime
from music_downloader.base import BaseSong, BasePlaylist


class YouTubeSong(BaseSong):
    
    def __init__(self, url: str):
        super().__init__(url)

    def get_platform(self) -> str:
        return "YouTube"

    @staticmethod
    def is_url_valid(url: str) -> bool:
        return "youtube.com/watch?" in url

    # def scrape_song_info(self) -> Dict[str, str]:
    #     """Extracts song information using pytube."""
    #     yt = YouTube(self.url)
        
    #     info = {
    #         "artist": yt.author,  # Equivalent to 'uploader' in yt_dlp
    #         "song": yt.title,
    #         "embed_url": f"https://www.youtube.com/embed/{yt.video_id}",
    #     }

    #     # Format title to include artist if needed
    #     if ' - ' not in info["song"]:
    #         info["song"] = f"{info['song']} by {info['artist']}"

    #     return info

    # def _download_audio(self, verbose: int = 0) -> bytes:
    #     """Downloads the audio and caches it in the _audio attribute using pytube, storing it in memory."""
    #     if self._audio is None:
    #         if verbose >= 1:
    #             print(f"...Downloading audio for '{self.title}': {self.url}")

    #         # Download audio stream
    #         yt = YouTube(self.url)
    #         audio_stream = yt.streams.filter(only_audio=True).first()

    #         # Read audio data into memory
    #         audio_buffer = BytesIO()
    #         audio_stream.stream_to_buffer(audio_buffer)
    #         audio_buffer.seek(0)  # Reset buffer position

    #         self._audio = audio_buffer

    #     return self._audio

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

    @property
    def audio_format(self) -> Dict[str, Any]:
        return {
            'format': 'audio/m4a',
            'audioformat': 'm4a',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',  # m4a uses aac encoding
                'preferredquality': '192',
            }],
        }

class YouTubePlaylist(BasePlaylist):
    
    def __init__(self, url: str):
        super().__init__(url)
    
    def get_platform(self) -> str:
        return "YouTube"

    @staticmethod
    def is_url_valid(url: str) -> bool:
        return "youtube.com/playlist?" in url

    def scrape_playlist_info(self) -> Dict[str, Union[str, List[str]]]:
        ydl_opts = {"quiet": True, "extract_flat": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=False)
        info["title"] = info.get("title", "Unknown Title")
        info["curator"] = info.pop("uploader", "Unknown Curator")
        info["song_urls"] = [s['url'] for s in info.get('entries', [])]
        info["embed_url"] = f"https://www.youtube.com/embed/{info.get('id')}" if info.get("id") else None
        return info

    # def scrape_playlist_info(self) -> Dict[str, Union[str, List[str]]]:
    #     # Extract playlist details using pytube
    #     playlist = Playlist(self.url)
    #     videos = [YouTube(url) for url in playlist.video_urls]  # Need to create YouTube objects
    #     info = {
    #         "title": playlist.title or "Unknown Title",
    #         "curator": "Unknown Curator",  # pytube does not provide the owner
    #         "song_urls": playlist.video_urls,
    #         "embed_url": f"https://www.youtube.com/embed/{videos[0].video_id}" if videos else None,
    #         "thumbnail": videos[0].thumbnail_url if videos else ""
    #     }
    #     return info

    # def create_song(self, url: str):
    #     return YouTubeSong(url)
    
    @property
    def thumbnail(self) -> str:
        return self.info.get("thumbnail")
