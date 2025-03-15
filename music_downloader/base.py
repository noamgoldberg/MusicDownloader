import logging
from abc import ABC, abstractmethod
from typing import List, Union, Dict, Optional
from io import BytesIO
from stqdm import stqdm as st_tqdm
import tempfile
import yt_dlp

from utils.file_utils import format_safe_filename
from utils.zip_utils import zip_audio_files

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()  # Currently set to stdout
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class BaseSong(ABC):
    
    ENTITY_TYPE = "song"
    
    def __init__(self, url: str):
        logger.debug(f"Initializing BaseSong with URL: {url}")
        self.url = url.strip()
        self.entity_type = self.ENTITY_TYPE
        self.platform = self.get_platform()
        self.download_from = self.get_download_platform()
        self._info = self.scrape_song_info()
        self._audio = None
        logger.info(f"Song initialized: {self.url} (Platform: {self.platform})")

    @abstractmethod
    def get_platform(self) -> str:
        pass

    def get_download_platform(self) -> str:
        return self.platform

    @abstractmethod
    def is_url_valid(url: str) -> bool:
        pass

    @abstractmethod
    def scrape_song_info(self) -> Dict[str, Union[str, None]]:
        pass
    
    @property
    def info(self) -> Dict[str, str]:
        if self._info is None:
            logger.debug(f"Scraping info for song: {self.url}")
            self._info = self.scrape_song_info()
        return self._info
    
    @property
    def title(self) -> str:
        return self.info.get("song", "Unknown Title")
    
    @property
    def artist(self) -> str:
        return self.info.get("artist", "Unknown Artist")

    @property
    def filename(self) -> str:
        title = format_safe_filename(self.title)
        artist = format_safe_filename(self.artist)
        return f"{title} by {artist}.mp3"
    
    @property
    def embed_url(self) -> str:
        return self.info.get("embed_url", None)
    
    @property
    def audio(self) -> BytesIO:
        logger.debug(f"Accessing audio for song: {self.title}")
        return self.download_audio()
    
    @audio.setter
    def audio(self, buffer: BytesIO):
        if not isinstance(buffer, BytesIO):
            raise TypeError("Invalid type for 'audio' property; expected BytesIO")
        logger.info(f"Setting audio buffer for song: {self.title}")
        self._audio = buffer
    
    def _download_audio(self, format: str = ".mp3", verbose: int = 0) -> bytes:
        """Downloads the audio and caches it in memory."""
        buffer = BytesIO()

        # Define a custom download function that writes to the buffer
        def write_to_buffer(d):
            if d['status'] == 'finished':
                buffer.seek(0)  # Reset buffer position for reading
                buffer.truncate()  # Clear buffer content to prevent overlap
                with open(d['filename'], 'rb') as f:
                    buffer.write(f.read())

        # Set up options for yt-dlp to download the audio
        ydl_opts = {
            'format': 'bestaudio/audio',
            'extractaudio': True,         # Extract audio only
            'audioformat': 'mp3',         # Convert to mp3
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': tempfile.gettempdir() + '/temp_audio_%(id)s.%(ext)s',  # Temporary file name with unique ID
            'progress_hooks': [write_to_buffer],  # Use custom hook to write to buffer
            'quiet': verbose == 0  # Set verbosity based on the verbose argument
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url])

        buffer.seek(0)  # Reset the buffer position before returning
        return buffer#.getvalue()  # Return the bytes in the buffer
    
    def download_audio(self, *, verbose: int = 0) -> bytes:
        if self._audio is None:
            logger.info(f"Downloading audio for song: {self.title}")
            self._audio = self._download_audio(verbose=verbose)
        return self._audio


class BasePlaylist(ABC):
    
    ENTITY_TYPE = "playlist"
    
    def __init__(self, url: str):
        logger.debug(f"Initializing BasePlaylist with URL: {url}")
        self.url = url.strip()
        self.entity_type = self.ENTITY_TYPE
        self._info = self.scrape_playlist_info()
        self.platform = self.get_platform()
        self.download_from = self.get_download_platform()
        self._songs = None
        self._audio = None
        self.current_batch_size = None
        self.audio_zipped = None
        logger.info(f"Playlist initialized: {self.title} (Platform: {self.platform})")

    @abstractmethod
    def get_platform(self) -> str:
        pass
    
    def get_download_platform(self) -> str:
        return self.platform

    @abstractmethod
    def is_url_valid(url: str) -> bool:
        pass

    @abstractmethod
    def scrape_playlist_info(self) -> Dict[str, Union[str, List[str]]]:
        pass

    @property
    def info(self) -> Dict[str, str]:
        if self._info is None:
            logger.debug("Scraping playlist info")
            self._info = self.scrape_playlist_info()
        return self._info

    @property
    def title(self) -> str:
        return self.info.get("title", "Unknown Title")
    
    @property
    def curator(self) -> str:
        return self.info.get("curator", "Unknown Curator")

    @property
    def song_urls(self) -> List[str]:
        return self.info.get("song_urls", [])

    def filename(self) -> str:
        return f"{format_safe_filename(self.title)}.zip"

    @property
    def embed_url(self) -> str:
        return self.info.get("embed_url")

    @abstractmethod
    def create_song(self, url: str) -> BaseSong:
        pass
    
    @property
    def songs(self) -> List[BaseSong]:
        if self._songs is None:
            logger.info(f"Creating song objects for playlist: {self.title}")
            self._songs = [self.create_song(url) for url in self.song_urls]
        return self._songs
    
    def get_num_tracks(self) -> int:
        return len(self.song_urls)

    @property
    def length(self) -> int:
        return self.get_num_tracks()

    @property
    @abstractmethod
    def thumbnail(self) -> str:
        pass

    @property
    def audio(self) -> List[BytesIO]:
        if self._audio is None:
            logger.info(f"Downloading all audio for playlist: {self.title}")
            self._audio = self.download_audio()
        return self._audio

    @audio.setter
    def audio(self, buffers: List[BytesIO]):
        if not isinstance(buffers, list) or not all(isinstance(elem, BytesIO) for elem in buffers):
            raise TypeError("Invalid type for 'audio' property; expected a list of BytesIO objects")
        logger.info(f"Setting audio buffers for playlist: {self.title}")
        self._audio = buffers

    def download_audio(self, *, stqdm: bool = False, verbose: int = 0) -> List[BytesIO]:
        if not self._audio:
            logger.info(f"Downloading {len(self.songs)} songs from playlist: {self.title}")
            audio = []
            desc = f"Downloading audio for {len(self.songs)} songs"
            songs = st_tqdm(self.songs, desc=desc) if stqdm else self.songs
            for i, song in enumerate(songs):
                if stqdm:
                    songs.set_description(f"{i + 1} / {len(self.songs)} Downloading: {song.title}")
                audio.append(song.download_audio(verbose=verbose))
            self._audio = audio
        return self._audio

    def zip_audio(self, *, batch_size: Optional[int] = None, stqdm: bool = False, verbose: int = 0) -> BytesIO:
        """Zip audio files of the playlist songs."""
        self.download_audio(stqdm=stqdm, verbose=verbose)
        if self.audio_zipped is None or batch_size != self.current_batch_size:
            self.current_batch_size = batch_size
            logger.info(f"Zipping {self.length} songs in playlist '{self.title}' with batch size: {batch_size}")
            self.audio_zipped = zip_audio_files(self.songs, batch_size=batch_size, stqdm=stqdm, total=self.length)
        return self.audio_zipped
