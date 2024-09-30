from typing import List, Dict, Optional, Literal
import time
import os
from io import BytesIO
import re
from stqdm import stqdm as st_tqdm

from patch.pytube_patch_oo import pytube
from pytube import YouTube, Playlist, Stream
# from patch.pytube_patch import PATCH_SCRIPT_FILEPATH, is_pytube_patched
from utils.zip_utils import zip_audio_files


# if not is_pytube_patched():
#     os.system("python patch/pytube_patch.py")
#     time.sleep(3)
#     if not is_pytube_patched():
#         raise AssertionError(
#             f"Must run {PATCH_SCRIPT_FILEPATH} patch script before using pytube-based "
#             f"custom YouTube classes: `python {PATCH_SCRIPT_FILEPATH}`"
#         )
    
class YouTubeVideo(YouTube):
    
    URL_FUNC = lambda url: "youtube.com/watch?" in url
    ENTITY_TYPE = "song"
    
    def __init__(self, url: str):
        super().__init__(url)
        self.artist = self.author
        self.url = self.watch_url
        self._title = self._format_song_title(self.title)
        self._audio_stream = None
        self._audio = None
        self.entity_type = YouTubeVideo.ENTITY_TYPE
        self.platform = "YouTube"
        self.download_from = "YouTube"
        self.current_batch_size = None

    def _format_song_title(self, title: str) -> str:
        if ' - ' not in title:
            title += f" by {self.artist}"
        return title

    @property
    def filename(self) -> str:
        """Returns the file name for the audio, formatted as .mp3."""
        return os.path.splitext(self.audio_stream.default_filename)[0] + '.mp3'

    @property
    def audio_stream(self) -> Stream:
        """Caches the audio stream to avoid redundant calls."""
        if self._audio_stream is None:
            self._audio_stream = self.streams.get_audio_only()
        return self._audio_stream

    @audio_stream.setter
    def audio_stream(self, stream: Stream):
        """Validates and sets the audio stream."""
        if not isinstance(stream, Stream):
            raise TypeError(f"Invalid type for 'audio_stream' property; expected pytube.Stream, got {type(stream).__name__}")
        self._audio_stream = stream

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
        if self._audio is None:  # Only download if not already cached
            if verbose >= 1:
                print(f"...Downloading audio for '{self.title}': {self.url}")
            buffer = BytesIO()
            self.audio_stream.stream_to_buffer(buffer)
            self.audio = buffer
            if verbose >= 1:
                print(f"......Successfully downloaded audio for '{self.title}'")
        else:
            if verbose >= 1:
                print(f"Audio for '{self.title}' is already downloaded.")
        return self._audio

class YouTubePlaylist(Playlist):
    
    URL_FUNC = lambda url: "youtube.com/playlist?" in url
    ENTITY_TYPE = "playlist"
    
    def __init__(self, url: str):
        super().__init__(url)
        self.url = self._input_url
        self._videos = None
        self.filename = os.path.join(self.title.replace(' ', '_'), '.zip')
        self.audio_zipped = None
        self.audio = None
        self.entity_type = YouTubePlaylist.ENTITY_TYPE
        self.platform = "YouTube"
        self.download_from = "YouTube"

    @property
    def videos(self):
        """Cache videos to ensure they are not re-instantiated."""
        if self._videos is None:
            self._videos = [YouTubeVideo(url) for url in self.video_urls]
        return self._videos

    def videos_generator(self):
        for video in self._videos:
            yield video

    @property
    def embed_url(self) -> str:
        """Extracts the YouTube playlist embed URL from a given playlist URL."""
        match = re.search(r'list=([a-zA-Z0-9_-]+)', self.url)
        if match:
            playlist_id = match.group(1)
            embed_url = f"https://www.youtube.com/embed/videoseries?list={playlist_id}"
            return embed_url
        else:
            raise ValueError("Invalid YouTube playlist URL")

    def download_audio(
        self,
        *,
        stqdm: bool = False,
        verbose: int = 0
    ) -> bytes:
        if self.audio is None:  # Ensure we only download once
            self.audio = []
            desc = f"Downloading audio for {self.length} videos in '{self.title}' playlist"
            videos = st_tqdm(self.videos, desc=desc) if stqdm else self.videos
            for i, video in enumerate(videos):
                if stqdm:
                    videos.set_description(f"{i + 1} / {self.length} Downloading: {video.title}")
                self.audio.append(
                    video.download_audio(
                        verbose=verbose
                    )
                )
        return self.audio

    def zip_audio(
        self,
        *,
        batch_size: Optional[int] = None,
        stqdm: bool = False,
        verbose: int = 0
    ) -> BytesIO:
        """Zip audio files of the playlist songs."""
        self.download_audio(
            stqdm=stqdm,
            verbose=verbose
        )
        audio_not_yet_zipped = self.audio_zipped is None
        batch_size_changed = batch_size != self.current_batch_size
        if audio_not_yet_zipped or batch_size_changed:
            self.current_batch_size = batch_size
            desc = f"Zipping audio for {self.length} songs in '{self.title}' playlist"
            if batch_size:
                if batch_size < self.length:
                    desc += f" (batches of {batch_size})"
                else:
                    batch_size = None
            self.audio_zipped = zip_audio_files(self.songs, batch_size=batch_size, stqdm=stqdm, total=self.length)
        return self.audio_zipped
