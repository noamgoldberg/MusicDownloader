from typing import Union, List, Any, Dict, Optional
from core.display.details import (
    display_title_and_url,
    display_entity_platform_label,
    display_embed, display_download_from_message
)
from core.display.download import prepare_playlist_download_kwargs, display_download_buttons
import streamlit as st

from music_downloader.youtube import YouTubePlaylist
from music_downloader.spotify import SpotifyPlaylist
from music_downloader.soundcloud import SoundCloudPlaylist


class PlaylistDisplay:
    
    ENTITY_TYPE = "playlist"
    
    def __init__(
        self,
        playlist_object: Union[YouTubePlaylist, SpotifyPlaylist, SoundCloudPlaylist]
    ):
        self.entity = playlist_object

    def display_playlist_details(self, embed_url: Optional[str]) -> None:
        """Displays playlist details."""
        entity = self.entity
        entity_type = PlaylistDisplay.ENTITY_TYPE
        display_title_and_url(
            title=entity.title,
            url=entity.url,
            entity_type=entity_type
        )
        display_entity_platform_label(entity.platform, entity_type)
        if embed_url:
            display_embed(embed_url)
        display_download_from_message(
            entity_type=entity_type, 
            download_from=entity.download_from
        )
        st.write(f"**Number of Songs**: {entity.length}")

    def display(self) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Displays playlist and handles download."""
        entity = self.entity
        self.display_playlist_details(entity.embed_url)
        batch_size = st.number_input(
            "Batch size (# of songs per file):",
            min_value=1,
            max_value=entity.length,
            value=min(st.session_state["default_batch_size"], entity.length)
        )
        is_audio_zipped = entity.audio_zipped is not None
        actions_str = "Zipping" if is_audio_zipped else "Downloading & Zipping"
        with st.spinner(f"{actions_str} Audio for {entity.length} items..."):
            audio_zipped = entity.zip_audio(batch_size=batch_size, stqdm=True)
        download_kwargs = prepare_playlist_download_kwargs(
            audio_zipped=audio_zipped,
            num_songs=entity.length,
            title=entity.title,
            batch_size=batch_size,
        )
        display_download_buttons(
            download_kwargs=download_kwargs,
            num_songs=entity.length,
            batch_size=batch_size,
            batch_buttons=True,
            columns=None
        )
        return {"num_songs": entity.length, "download_kwargs": download_kwargs}
