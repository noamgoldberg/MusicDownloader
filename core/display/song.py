from typing import Any, Dict, Optional, List, Union
from core.display.details import display_entity_platform_label, display_title_and_url, display_embed, display_download_from_message
from core.display.download import prepare_song_download_kwargs, display_download_buttons
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from music_downloader.youtube import YouTubeVideo
from music_downloader.spotify import SpotifySong
from music_downloader.soundcloud import SoundCloudSong


class SongDisplay:
    
    ENTITY_TYPE = "song"
    
    def __init__(
        self,
        song_object: Union[YouTubeVideo, SpotifySong, SoundCloudSong]
    ):
        self.entity = song_object

    def display_song_details(self, url: str, embed_url_1: str, embed_url_2: Optional[str]) -> Optional[List[DeltaGenerator]]:
        """Displays song details."""
        entity = self.entity
        entity_type = SongDisplay.ENTITY_TYPE
        display_title_and_url(
            url=url,
            title=f"{entity.title} by {entity.artist}",
            entity_type=entity_type
        )
        display_entity_platform_label(entity.platform, entity_type)
        display_embed(embed_url_1)
        
        columns = st.columns(2) if embed_url_2 else None
        display_download_from_message(
            entity_type=entity_type,
            download_from=entity.download_from,
            columns=columns
        )
        if embed_url_2:
            with columns[1]:
                display_embed(embed_url_2)
        return columns

    def display(self) -> Dict[str, Any]:
        """Displays song and handles download."""
        entity = self.entity
        if entity.platform == "Spotify":
            url = entity.spotify_url
            embed_url_1 = getattr(entity, 'spotify_embed_url', None)
            embed_url_2 = getattr(entity, 'youtube_embed_url', None)
        else:
            url, embed_url_1, embed_url_2 = entity.url, entity.embed_url, None
        columns = self.display_song_details(url, embed_url_1, embed_url_2)
        with st.spinner(f"Downloading Audio for {entity.title}..."):
            buffer = entity.download_audio()
        download_kwargs = prepare_song_download_kwargs(buffer=buffer, title=entity.title, filename=entity.filename)
        display_download_buttons(
            download_kwargs=download_kwargs,
            num_songs=1,
            batch_size=None,
            batch_buttons=True,
            columns=columns,
        )
        return {"num_songs": 1, "download_kwargs": download_kwargs}