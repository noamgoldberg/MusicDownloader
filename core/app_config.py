import streamlit as st


def configure_app():
    st.set_page_config(
        page_title="Music Downloader",
        page_icon="🎵",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
