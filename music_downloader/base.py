from abc import ABC, abstractmethod
from typing import List, Union, Dict
from io import BytesIO


class BaseSong(ABC):
    ENTITY_TYPE = "song"
    
    def __init__(self, url: str):
        self.url = url.strip()
        self._song_info = None
        self._title = None
        self._artist = None
        self._embed_url = None
        self._audio = None
        self.platform = self.get_platform()
        self.entity_type = self.ENTITY_TYPE
        self.download_from = self.platform

    @abstractmethod
    def get_platform(self) -> str:
        pass

    @abstractmethod
    def scrape_song_info(self) -> Dict[str, Union[str, None]]:
        pass
    
    @property
    def song_info(self) -> Dict[str, str]:
        if self._song_info is None:
            self._song_info = self.scrape_song_info()
        return self._song_info
    
    @property
    def title(self) -> str:
        return self.song_info["song"]
    
    @property
    def artist(self) -> str:
        return self.song_info["artist"]

    @property
    def filename(self) -> str:
        title = self.title \
            .replace(' /', ' -').replace('/ ', '- ').replace('/', '-') \
            .replace(' \\', ' -').replace('\\ ', '- ').replace('\\', '-')
        return f"{title} by {self.artist}.mp3"
    
    @property
    def embed_url(self) -> str:
        return self.song_info["embed_url"]
    
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
        attrs = self.scrape_playlist_info()
        self.title = attrs["title"]
        self.curator = attrs["curator"]
        self.song_urls = attrs["song_urls"]
        self._songs = None
        self.filename = f"{self.title.replace(' ', '_')}.zip"
        self.audio = None
        self.audio_zipped = None
        self.platform = self.get_platform()
        self.entity_type = self.ENTITY_TYPE
        self.download_from = self.platform
        self.embed_url = None
        self.current_batch_size = None
    
    @abstractmethod
    def scrape_playlist_info(self) -> Dict[str, Union[str, List[str]]]:
        pass
    
    @property
    def length(self) -> int:
        return len(self.song_urls)
    
    @property
    def songs(self):
        if self._songs is None:
            self._songs = [self.create_song(url) for url in self.song_urls]
        return self._songs
    
    @abstractmethod
    def create_song(self, url: str):
        pass
    
    def songs_generator(self):
        for song in self.songs:
            yield song
    
    def get_playlist_titles(self) -> List[str]:
        return [song.title for song in self.songs]
    
    def get_playlist_urls(self) -> List[str]:
        return [song.url for song in self.songs]
    
    def get_playlist_dict(self) -> Dict[str, str]:
        return {song.title: song.url for song in self.songs}
    
    @abstractmethod
    def get_platform(self) -> str:
        pass
