from typing import List, Union, Dict, Optional
import os
from io import BytesIO
from stqdm import stqdm as st_tqdm
import yt_dlp
from utils.selenium_utils import get_driver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
import re
import tempfile
import streamlit as st

from utils.selenium_utils import try_find_element, try_find_elements, click_element_close_model
from utils.zip_utils import zip_audio_files


def is_soundcloud_playlist(url: str) -> bool:
    # Regex to match 'sets' in the second part of the path after the artist name
    pattern = r"soundcloud\.com\/[^\/]+\/sets\/[^\/]+"
    return bool(re.search(pattern, url))

@st.cache_resource
def get_driver(
    headless: bool = True,
    disable_gpu: bool = True,
    no_sandbox: bool = True,
    disable_dev_shm_usage: bool = True,
) -> webdriver.Chrome:
    return get_driver(
        headless=headless,
        disable_gpu=disable_gpu,
        no_sandbox=no_sandbox,
        disable_dev_shm_usage=disable_dev_shm_usage,
    )

class SoundCloudSong:
    
    URL_FUNC = lambda url: ("soundcloud.com/" in url) and (not is_soundcloud_playlist(url))
    ENTITY_TYPE = "song"
    
    def __init__(self, url: str):
        self.url = url.strip()
        self._song_info = None
        self.get_driver = get_driver
        self._title = None
        self._artist = None
        self._embed_url = None
        self.filename = f"{self.title} by {self.artist}.mp3"
        self._audio = None
        self.platform = "SoundCloud"
        self.entity_type = SoundCloudSong.ENTITY_TYPE
        self.download_from = self.platform

    @staticmethod
    def _get_embed_url(driver: webdriver.Chrome) -> Union[str, None]:
        share_button = try_find_element(driver, By.CSS_SELECTOR, 'button[title="Share"]')
        if share_button is not None:
            # click_element(share_button, sleep=2)
            click_element_close_model(driver, share_button, sleep=2)
            embed_tab = try_find_element(driver, By.LINK_TEXT, 'Embed')
            if embed_tab is not None:
                # click_element(embed_tab, sleep=2)
                click_element_close_model(driver, embed_tab, sleep=2)
                iframes = try_find_elements(driver, by=By.CSS_SELECTOR, value="iframe", wait=True, timeout=10)
                embed_urls = [i.get_attribute("src") for i in iframes]
                embed_urls = list(set([url for url in embed_urls if "api.soundcloud" in url]))
                if len(embed_urls) == 1:
                    return embed_urls[0]
      
    def scrape_song_info(self) -> Dict[str, Union[str, None]]:
        driver = self.get_driver(
            headless=True,
            disable_gpu=True,
            no_sandbox=True,
            disable_dev_shm_usage=True,
        )
        driver.get(self.url)
        info = {}
        for var_name, css_elem in [("song", "h1"), ("artist", "h2")]:
            value = try_find_element(driver, By.CSS_SELECTOR, css_elem)
            info[var_name] = value if value is None else value.text
        if info["song"] is None:
            raise Exception(f"Failed to extract song title and artist/username for {self.url}")
        try:
            info["embed_url"] = self._get_embed_url(driver)
        except StaleElementReferenceException:  # retry
            info["embed_url"] = self._get_embed_url(driver)
        driver.quit()
        return info

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
    def embed_url(self) -> str:
        return self.song_info["embed_url"]

    @property
    def audio(self) -> BytesIO:
        """Returns the cached audio if already downloaded, otherwise downloads it."""
        return self.download_audio()

    @audio.setter
    def audio(self, buffer: BytesIO):
        """Validates and sets the audio buffer."""
        if not isinstance(buffer, BytesIO):
            raise TypeError(f"Invalid type for 'audio' property; expected BytesIO, got {type(buffer).__name__}")
        self._audio = buffer

    def _download_audio(self, verbose: int = 0) -> bytes:
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
            'format': 'audio/mp3',  # Download the best audio quality
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

    def download_audio(
        self,
        *,
        verbose: int = 0
    ) -> bytes:
        """Downloads the audio and caches it in the _audio attribute, keeping it in memory."""
        if self._audio is None:  # Only download if not already cached
            self._audio = self._download_audio(
                verbose=verbose
            )
        return self._audio

class SoundCloudPlaylist:
    
    URL_FUNC = lambda url: ("soundcloud.com/" in url) and (is_soundcloud_playlist(url))
    ENTITY_TYPE = "playlist"
    
    def __init__(self, url: str):
        self.url = url.strip()
        attrs = self.scrape_playlist_info()
        self.title = attrs["title"]
        self.curator = attrs["curator"]
        self.song_urls = attrs["song_urls"]
        self._songs = None
        self.filename = os.path.join(self.title.replace(' ', '_'), '.zip')
        self.audio = None
        self.audio_zipped = None
        self.platform = "SoundCloud"
        self.entity_type = SoundCloudPlaylist.ENTITY_TYPE
        self.download_from = self.platform
        self.embed_url = None
        self.current_batch_size = None
        self.get_driver = get_driver

    def scrape_playlist_info(self):
        driver = self.get_driver(
            headless=True,
            disable_gpu=True,
            no_sandbox=True,
            disable_dev_shm_usage=True,
        )
        driver.get(self.url)  # Replace with your target URL
        titles_text = try_find_elements(driver, by=By.CLASS_NAME, value="soundTitle", wait=True, timeout=10)
        if titles_text is None:
            raise Exception(f"Failed to extract playlist title and curator for SoundCloud playlist: {self.url}")
        titles_text = titles_text[0].text
        titles_text_split = titles_text.strip().split('\n')
        title, curator = titles_text_split[1], titles_text_split[2].rstrip("Verified").strip()
        song_elems = try_find_elements(driver, by=By.CLASS_NAME, value="trackItem__trackTitle", wait=True, timeout=10)
        song_urls = [song_elem.get_attribute("href") for song_elem in song_elems]
        driver.quit()
        return {
            "title": title, 
            "curator": curator,
            "song_urls": song_urls,
        }

    @property
    def length(self) -> int:
        return len(self.song_urls)

    @property
    def songs(self):
        """Cache songs to ensure they are not re-instantiated."""
        if self._songs is None:
            self._songs = [SoundCloudSong(url) for url in self.song_urls]
        return self._songs

    def songs_generator(self):
        for song in self.songs:
            yield song

    def get_playlist_titles(self) -> List[str]:
        """Return a list of titles for all songs in the playlist."""
        return [song.title for song in self.songs]

    def get_playlist_urls(self) -> List[str]:
        """Return a list of URLs for all songs in the playlist."""
        return [song.url for song in self.songs]

    def get_playlist_dict(self) -> Dict[str, str]:
        """Return a list of titles and URLs for all songs in the playlist."""
        return {song.title: song.url for song in self.songs}

    def download_audio(
        self,
        *,
        stqdm: bool = False,
        verbose: int = 0
    ) -> List[bytes]:
        if self.audio is None:  # Ensure we only download once
            self.audio = []
            desc = f"Downloading audio for {self.length} songs in '{self.title}' playlist"
            songs = st_tqdm(self.songs, desc=desc) if stqdm else self.songs
            for i, song in enumerate(songs):
                if stqdm:
                    songs.set_description(f"{i + 1} / {self.length} Downloading: {song.title}")
                self.audio.append(song.download_audio(
                    verbose=verbose
                ))
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
