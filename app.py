import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

from core.app_config import configure_app
from core.session import update_session_state
from core.display import display_url
from core.display.utils import display_labels, display_urls_list
from utils.io_utils import get_size
from utils.url_utils import extract_and_clean_urls
from utils.func_utils import get_unique_elems_ordered
from utils.zip_utils import zip_audio_files


def launch_app():
    st.title("🎵 Music Downloader")
    display_labels(
        [":green[Spotify]", ":red[YouTube]", ":orange[SoundCloud]"],
        font_size=16,
        border_radius=7,
    )
    st.info("👇 Enter a URL or list of URLs of a song/video or playlist from Spotify, YouTube, or Soundcloud")
    input_str = st.text_area("Enter URLs here:", key="input_str_field", height=150)
    warning_container = st.empty()
    download_all_button = st.empty()
    st.session_state["urls"] = st.session_state.get("urls", {})
    urls = get_unique_elems_ordered(extract_and_clean_urls(input_str))
    update_session_state(urls)
    display_urls_list("Click here to see extracted URLs", urls)
    st.session_state["default_batch_size"] = 50
    data = {}
    data_limit, units, total_size, total_songs = 2, "gb", 0, 0
    for i, url in enumerate(urls):
        with st.container(border=True):
            results = display_url(url)
            num_songs, download_kwargs = results
            download_kwargs = [download_kwargs] if isinstance(download_kwargs, dict) else download_kwargs
            if download_kwargs:
                for kwargs in download_kwargs:
                    data_iter, filename = kwargs["data"], kwargs["file_name"]
                    data[filename] = BytesIO(data_iter) if isinstance(data_iter, bytes) else data_iter
                    total_size += sum([get_size(buf, units=units) for _, buf in data.items()])
                    total_songs += num_songs
                    if total_size > data_limit:
                        with warning_container:
                            st.warning(
                                f"Warning: The total data size exceeds the {data_limit} {units.upper()}"
                                "limit, the number of downloads has been capped"
                            )
                            included = list(pd.Index(data.keys()).intersection(urls))
                            excluded = list(pd.Index(data.keys()).difference(urls))
                            display_urls_list("URLs Extracted", included)
                            display_urls_list("URLs Not Extracted", excluded)
                            break
    if len(urls) >= 2:
        with download_all_button:
            with st.spinner(f"Zipping all audio into single zip file..."):
                all_songs_zipped = zip_audio_files(data, stqdm=True, total=len(data))
            st.download_button(
                label=f"Download All {total_songs} Songs (.zip)",
                data=all_songs_zipped,
                file_name=f"all_songs_{str(datetime.today()).split()[0]}.zip",
                mime="application/zip",
            )
    

def main():
    configure_app()
    launch_app()

if __name__ == "__main__":
    main()
