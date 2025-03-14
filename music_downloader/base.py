from abc import ABC, abstractmethod
from typing import List, Union, Dict, Optional
import numpy as np
from io import BytesIO
from stqdm import stqdm as st_tqdm

from utils.file_utils import format_safe_filename
from utils.zip_utils import zip_audio_files


class BaseSong(ABC):
    
    ENTITY_TYPE = "song"
    
    def __init__(self, url: str):
        self.url = url.strip()
        self.entity_type = self.ENTITY_TYPE
        self.platform = self.get_platform()
        self.download_from = self.get_download_platform()
        self._info = self.scrape_song_info()
        self._audio = None

    @abstractmethod
    def get_platform() -> str:
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
        return self.download_audio()
    
    @audio.setter
    def audio(self, buffer: BytesIO):
        if not isinstance(buffer, BytesIO):
            raise TypeError("Invalid type for 'audio' property; expected BytesIO")
        self._audio = buffer
    
    @abstractmethod
    def _download_audio(self, verbose: int = 0) -> bytes:
        pass
    
    def download_audio(self, *, verbose: int = 0) -> bytes:
        if self._audio is None:
            self._audio = self._download_audio(verbose=verbose)
        return self._audio


class BasePlaylist(ABC):
    
    ENTITY_TYPE = "playlist"
    
    def __init__(self, url: str):
        self.url = url.strip()
        self.entity_type = self.ENTITY_TYPE
        self._info = self.scrape_playlist_info()
        self.platform = self.get_platform()
        self.download_from = self.get_download_platform()
        self._songs = None
        self._audio = None
        self.current_batch_size = None
        self.audio_zipped = None

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
            self._info = self.scrape_playlist_info()
        return self._info

    @property
    def title(self) -> str:
        return self.info.get("title", "Unknown Title")
    
    @property
    def curator(self) -> str:
        return self.info.get("curator", "Unknown Curator")

    @property
    def song_urls(self) -> str:
        return self.info["song_urls"]

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
            self._songs = [self.create_song(url) for url in self.info["song_urls"]]
        return self._songs
    
    def songs_generator(self):
        for song in self.songs:
            yield song

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
            self._audio = self.download_audio()
        return self._audio

    @audio.setter
    def audio(self, buffers: List[BytesIO]):
        if not isinstance(buffers, list):
            raise TypeError(f"{type(buffers).__name__}: Invalid type for 'audio' property; expected 'list'")
        elif not all(isinstance(elem, BytesIO) for elem in buffers):
            raise TypeError(
                f"{np.unique(type(e).__name__ for e in buffers)}: "
                "Invalid type/s for 'audio' property; expected a list of exclusively BytesIO objects"
            )
        self._audio = buffers

    def download_audio(self, *, stqdm: bool = False, verbose: int = 0) -> List[BytesIO]:
        if not self._audio:
            audio = []
            desc = f"Downloading audio for {len(self.songs)} songs"
            songs = st_tqdm(self.songs, desc=desc) if stqdm else self.songs
            for i, song in enumerate(songs):
                if stqdm:
                    songs.set_description(f"{i + 1} / {len(self.songs)} Downloading: {song.title}")
                audio.append(song.download_audio(verbose=verbose))
            self._audio = audio  # Directly assign to _audio to avoid triggering the setter
        return self._audio

    def zip_audio(
        self,
        *,
        batch_size: Optional[int] = None,
        stqdm: bool = False,
        verbose: int = 0
    ) -> BytesIO:
        """Zip audio files of the playlist songs."""
        self.download_audio(stqdm=stqdm, verbose=verbose)
        if self.audio_zipped is None or batch_size != self.current_batch_size:
            self.current_batch_size = batch_size
            desc = f"Zipping audio for {self.length} songs in '{self.title}' playlist"
            if batch_size and batch_size < self.length:
                desc += f" (batches of {batch_size})"
            self.audio_zipped = zip_audio_files(self.songs, batch_size=batch_size, stqdm=stqdm, total=self.length)
        return self.audio_zipped