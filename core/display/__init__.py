from typing import Union, Tuple, Dict
import os
import streamlit as st
from streamlit.runtime.secrets import SECRETS_FILE_LOCS
from io import BytesIO
import yt_dlp
from spotipy.exceptions import SpotifyException
from copy import deepcopy

from music_downloader.youtube import YouTubeVideo, YouTubePlaylist
from music_downloader.spotify import SpotifySong, SpotifyPlaylist
from music_downloader.soundcloud import SoundCloudSong, SoundCloudPlaylist
from core.display.display import Display


ENTITY_CLASSES = {
    "YouTube": {
        "song": YouTubeVideo,
        "playlist": YouTubePlaylist,
    },
    "Spotify": {
        "song": SpotifySong,
        "playlist": SpotifyPlaylist,
    },
    "SoundCloud": {
        "song": SoundCloudSong,
        "playlist": SoundCloudPlaylist,
    },
}

def get_entity_class_from_url(url: str) -> Tuple[Union[str, None], Union[str, None], Union[type, None]]:
    """
    Retrieve the appropriate platform, entity type, and class based on the URL.
    
    Returns:
        platform (str): The platform name (YouTube, Spotify, SoundCloud) or None if not found.
        entity_type (str): The entity type ('song' or 'playlist') or None if not found.
        entity_class (type): The entity class (YouTubeVideo, SpotifySong, etc.) or None if not found.
    """
    for platform, platform_dict in ENTITY_CLASSES.items():
        for entity_type, entity_class in platform_dict.items():
            if entity_class.URL_FUNC(url):  # Assumes URL_FUNC checks if the URL matches the entity's platform
                return platform, entity_type, entity_class
    return None, None, None

def get_platform_credentials(platform: str) -> Dict[str, str]:
    if any([os.path.exists(path) for path in SECRETS_FILE_LOCS]):
        platform = platform.lower()
        if platform == "spotify":
            keys = ["client_id", "client_secret", "redirect_uri"]
            return {f"{platform}_{key}": st.secrets[platform][key] for key in keys}
    return {}

def apply_st_cache_selenium_driver(entity: Union[
    YouTubeVideo, YouTubePlaylist,
    SpotifySong, SpotifyPlaylist,
    SoundCloudSong, SoundCloudPlaylist
]) -> None:
    # pass
    if hasattr(entity, "get_driver"):
        @st.cache_resource
        def get_driver_cached(*args, **kwargs):
            func = deepcopy(entity.get_driver)
            return func(*args, **kwargs)
        entity.get_driver = get_driver_cached

def display_url(url: str) -> Union[BytesIO, Tuple[int, dict]]:
    """
    Main function to display the appropriate entity based on the platform and type.
    
    Parameters:
        url (str): The URL to be processed and displayed.
    
    Returns:
        Tuple[int, dict]: The number of songs and download kwargs, or None if an error occurs.
    """
    if url:
        exception_map = {
            SpotifyException: "Spotify (Spotipy API)",
            yt_dlp.utils.DownloadError: "YouTube (YouTubeDL API)"
        }
        try:
            platform, entity_type, entity_class = get_entity_class_from_url(url)
            if platform and entity_type:
                # Initialize session state if necessary
                st.session_state["urls"] = st.session_state.get("urls", {})
                st.session_state["urls"][url] = st.session_state["urls"].get(url, {})

                # Initialize the entity object in the session state if not already present
                if "entity" not in st.session_state["urls"][url]:
                    st.session_state["urls"][url]["entity"] = entity_class(url=url, **get_platform_credentials(platform))
                entity = st.session_state["urls"][url]["entity"]
                
                # Add st.cache to get_driver Selenium method of entity
                apply_st_cache_selenium_driver(entity)
                
                # Create a Display object to display the song or playlist
                display_func = Display(entity).display

                # Call the display method, which returns the number of songs and download kwargs
                url_results = display_func()
                num_songs = url_results["num_songs"]
                download_kwargs = url_results["download_kwargs"]
                return num_songs, download_kwargs
            
            else:
                st.error(f"Invalid URL and/or unsupported platform: {url}")
                return None, {}
        except tuple(exception_map.keys()) as e:
            for exc_type, exc_platform in exception_map.items():
                if isinstance(e, exc_type):
                    st.error(f"{exc_platform} exception occurred. Failed to extract song/playlist from URL: {url}")
                    st.error(f"Error: {e}")
                    break
            return None, {}
    else:
        return None, {}
