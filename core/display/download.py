import streamlit as st
from typing import Dict, Any, Union, List, Optional
from pathlib import Path
from streamlit.delta_generator import DeltaGenerator

from utils.zip_utils import zip_audio_files


def prepare_song_download_kwargs(
    *,
    buffer: bytes,
    title: str,
    filename: str,
) -> Dict[str, Any]:
    """Prepare the download button data for the song."""
    return {
        "label": "Download Song",
        "key": f"download_song_{title}",
        "data": buffer,
        "file_name": filename,
        "mime": "audio/mp3",
    }

def prepare_playlist_download_kwargs(
    *,
    audio_zipped: Union[bytes, List[bytes]],
    num_songs: int,
    title: str,
    batch_size: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Prepare download data for the playlist."""
    if isinstance(audio_zipped, list):
        if batch_size is None:
            raise Exception(
                "Batch size invalid; batch_size param cannot be "
                "None when the songs are zipped in batches"
            )
        download_kwargs = []
        for idx, zipped_buffer in enumerate(audio_zipped):
            start = idx * batch_size + 1
            end = min(start + batch_size - 1, num_songs)
            download_kwargs.append({
                "label": f"Download Songs {start} to {end} (.zip)",
                "data": zipped_buffer,
                "file_name": f"{title} - Songs {start} to {end}.zip",
                "mime": "application/zip",
            })
        return download_kwargs
    else:
        return [{
            "label": f"Download {num_songs} Songs (.zip)",
            "data": audio_zipped,
            "file_name": title,
            "mime": "application/zip",
        }]

def display_download_buttons(
    *,
    download_kwargs: Union[Dict[str, Any], List[Dict[str, Any]]],
    num_songs: int,
    batch_size: int,
    batch_buttons: bool = True,
    columns: Optional[DeltaGenerator] = None
):
    """Display download buttons, either for each batch or as a single combined batch."""
    if not isinstance(download_kwargs, list):
        download_kwargs = [download_kwargs]
    def _display_download_button():
        if len(download_kwargs) > 1:
            all_data = {kwargs["file_name"]: kwargs["data"] for kwargs in download_kwargs}
            all_songs_zip = zip_audio_files(all_data, stqdm=True, batch_size=None)
            filename = Path(download_kwargs[0]["file_name"]).stem.split('-')[0].strip()
            filename += f' - All Songs (Batches of {batch_size}).zip'
            st.download_button(
                label=f"Download All {num_songs} Songs (Batches of {batch_size}) (.zip)",
                data=all_songs_zip,
                file_name=filename,
                mime="application/zip",
            )
            if not batch_buttons:
                return
        for kwargs in download_kwargs:
            st.download_button(**kwargs)
    if columns is None:
        _display_download_button()
    else:
        with columns[0]:
            _display_download_button()
            