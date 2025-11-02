from typing import List, Union, Dict, Any
import time
import re
import tempfile
import os
from io import BytesIO
import yt_dlp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


from music_downloader.base import BaseSong, BasePlaylist
from utils.selenium_utils import (
    initialize_driver,
    try_find_element,
    try_find_elements,
    click_element_close_model
)


def scrape_soundcloud_embed_url(
    url: str,
    driver: webdriver.Chrome = None,
    headless: bool = True,
    disable_gpu: bool = True,
    no_sandbox: bool = True,
    disable_dev_shm_usage: bool = True
) -> Union[str, None]:
    if driver is None:
        driver = initialize_driver(
            headless=headless,
            disable_gpu=disable_gpu,
            no_sandbox=no_sandbox,
            disable_dev_shm_usage=disable_dev_shm_usage,
        )
    driver.get(url)
    share_button = try_find_element(driver, By.CSS_SELECTOR, 'button[title="Share"]')
    if share_button is not None:
        time.sleep(1)
        click_element_close_model(driver, share_button, sleep=2)
        embed_tab = try_find_element(driver, By.LINK_TEXT, 'Embed', timeout=20)
        if embed_tab is not None:
            time.sleep(1)
            click_element_close_model(driver, embed_tab, sleep=2)
            iframes = try_find_elements(driver, by=By.CSS_SELECTOR, value="iframe", wait=True, timeout=10)
            embed_urls = [i.get_attribute("src") for i in iframes]
            embed_urls = list(set([url for url in embed_urls if "api.soundcloud" in url]))
            if len(embed_urls) == 1:
                return embed_urls[0]

class SoundCloudSong(BaseSong):
    
    audio_format = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "audioformat": "m4a",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",
            "preferredquality": "192",
        }],
    }

    def __init__(self, url: str):
        super().__init__(url)

    @staticmethod
    def get_platform() -> str:
        return "SoundCloud"

    @staticmethod
    def is_url_valid(url: str) -> bool:
        if "soundcloud.com/" in url:
            return not SoundCloudPlaylist.is_url_playlist(url)
        return False
    
    def scrape_song_info(self) -> Dict[str, Union[str, None]]:
        driver = initialize_driver(
            headless=True,
            disable_gpu=True,
            no_sandbox=True,
            disable_dev_shm_usage=True
        )
        driver.get(self.url)
        info = {}
        for var_name, css_elem in [("song", "h1"), ("artist", "h2")]:
            value = try_find_element(driver, By.CSS_SELECTOR, css_elem)
            info[var_name] = value if value is None else value.text
        if info["song"] is None:
            raise Exception(f"Failed to extract song title and artist/username for {self.url}")
        info["embed_url"] = None
        # try:
        #     info["embed_url"] = scrape_soundcloud_embed_url(self.url, driver=driver)
        # except StaleElementReferenceException:  # retry
        #     info["embed_url"] = scrape_soundcloud_embed_url(self.url, driver=driver)
        driver.quit()
        return info

class SoundCloudPlaylist(BasePlaylist):
    
    def __init__(self, url: str):
        super().__init__(url)

    def get_platform(self) -> str:
        return "SoundCloud"

    @staticmethod
    def is_url_playlist(url: str) -> bool:
        # Regex to match 'sets' in the second part of the path after the artist name
        pattern = r"soundcloud\.com\/[^\/]+\/sets\/[^\/]+"
        return bool(re.search(pattern, url))

    @classmethod
    def is_url_valid(cls, url: str) -> bool:
        if "soundcloud.com/" in url:
            return cls.is_url_playlist(url)
        return False

    def scrape_playlist_info(self) -> Dict[str, str]:
        driver = initialize_driver(
            headless=True,
            disable_gpu=True,
            no_sandbox=True,
            disable_dev_shm_usage=True
        )
        driver.get(self.url)  # Replace with your target URL
        titles_text = try_find_elements(driver, by=By.CLASS_NAME, value="soundTitle", wait=True, timeout=10)
        if titles_text is None:
            raise Exception(f"Failed to extract playlist title and curator for SoundCloud playlist: {self.url}")
        titles_text = titles_text[0].text
        titles_text_split = titles_text.strip().split('\n')
        title, curator = titles_text_split[0], titles_text_split[1].rstrip("Verified").strip()

        previous_count = 0
        sleep_attempts = 0
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        while True:
            # Scroll to bottom
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
            time.sleep(0.5)

            # Get all currently loaded song elements
            song_elems = driver.find_elements(By.CLASS_NAME, "trackItem__trackTitle")
            current_count = len(song_elems)

            # Check if new songs loaded
            if current_count == previous_count:
                sleep_attempts += 1
                if sleep_attempts >= 3:
                    break  # stop after 3 attempts with no new songs
                time.sleep(1)  # wait a bit before trying again
            else:
                sleep_attempts = 0  # reset attempts if new songs loaded
                previous_count = current_count

        # Once done scrolling, extract URLs
        song_urls = [elem.get_attribute("href") for elem in song_elems if elem.get_attribute("href")]

        driver.quit()
        return {
            "title": title, 
            "curator": curator,
            "song_urls": song_urls,
            "embed_url": None,
            # "embed_url": scrape_soundcloud_embed_url(self.url, driver=driver)
        }

    def create_song(self, url: str) -> SoundCloudSong:
        return SoundCloudSong(url)

    @property
    def songs(self) -> List[SoundCloudSong]:
        """Cache songs to ensure they are not re-instantiated."""
        if self._songs is None:
            self._songs = [SoundCloudSong(url) for url in self.song_urls]
        return self._songs

    @property
    def thumbnail(self) -> str:
        return self.info.get("thumbnail")

