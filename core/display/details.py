from typing import List, Optional
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from core.display.utils import display_labels, display_embed_iframe


PLATFORM_COLORS = {
    "Spotify": "green",
    "YouTube": "red",
    "SoundCloud": "orange",
}
ENTITY_ICONS = {"song": "♫", "playlist": "💿"}

def display_entity_platform_label(platform: str, entity_type: str) -> None:
    """Displays platform-specific labels."""
    label = f":{PLATFORM_COLORS[platform]}[{platform} {entity_type.title()}]"
    display_labels(label, num_cols=1, font_size=16, border_radius=7)

def display_download_from_message(
    *,
    entity_type: str,
    download_from: str,
    columns: Optional[List[DeltaGenerator]] = None,
) -> None:
    if columns is not None:
        with columns[0]:
            st.write(f"_Note: This {entity_type} will be downloaded from {download_from}_")
    else:
        st.write(f"_Note: This {entity_type} will be downloaded from {download_from}_")

def display_title_and_url(
    *,
    title: str,
    url: str,
    entity_type: str,
) -> None:
    st.write(f"#### {ENTITY_ICONS[entity_type]} {title}")
    st.write(url)

def display_embed(url: str) -> None:
    """Helper function to display embedded content."""
    display_embed_iframe(url)
