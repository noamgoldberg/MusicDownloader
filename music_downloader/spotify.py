from typing import Optional, Union, Tuple, List, Dict
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from youtubesearchpython import VideosSearch
from dotenv import load_dotenv
from io import BytesIO
from stqdm import stqdm as st_tqdm
import re

from music_downloader.base import BaseSong, BasePlaylist
from music_downloader.youtube import YouTubeSong
from utils.zip_utils import zip_audio_files


load_dotenv()

def authenticate() -> spotipy.Spotify:
    """Authenticate Spotify API connection"""
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
            scope="playlist-read-private"
        )
    )

class SpotifySong(BaseSong):
    
    def __init__(
        self,
        url: Optional[str] = None,
        song: Optional[str] = None,
        artist: Optional[str] = None,
    ):
        if url or (song and artist):
            self.sp = self.authenticate()
            if song and artist:
                url = self.get_url_from_song(song, artist)
        else:
            raise Exception(f"{url=}, {song=}, {artist=}: Must provide either URL or Song & Artist to instantiate SpotifySong")
        self._youtube_url = None
        self._youtube_song = None
        self._youtube_embed_url = None
        super().__init__(url)

    def _validate_details(self, song: str, artist: str):
        for (param, value) in [("song", song), ("artist", artist)]:
            if value and value.strip().lower() != getattr(self, param, "").strip().lower():
                raise ValueError(f"Given {param} {value} does not match {param} extracted from given url, '{getattr(self, param)}'")

    @staticmethod
    def is_url_valid(url: str) -> bool:
        return "spotify.com/track" in url

    def scrape_song_info(self) -> Dict[str, str]:
        song, artist = self.get_song_details_from_spotify(self.url)
        self._validate_details(song, artist)
        embed_url = self.get_embed_url(self.url)
        return {
            "song": song,
            "artist": artist,
            "embed_url": embed_url,
        }

    def get_platform(self) -> str:
        return "Spotify"

    def get_download_platform(self) -> str:
        return "YouTube"

    @staticmethod
    def get_track_id(url: str) -> str:
        return re.search(r"track/([a-zA-Z0-9]+)", url).group(1)

    @property
    def track_id(self) -> str:
        return self.get_track_id(self.url)

    @staticmethod
    def is_url_valid(url: str) -> bool:
        return "spotify.com/track" in url

    def authenticate(self) -> spotipy.Spotify:
        return authenticate()

    def get_song_details_from_spotify(self, url: str) -> tuple:
        """Get song name and artist from Spotify URL."""
        track = self.sp.track(url)
        song_name = track['name']
        artist_name = track['artists'][0]['name']
        return song_name, artist_name

    def search_song_on_spotify(self, song: str, artist: str, limit: int = 5) -> List[Tuple[str, str, str]]:
        """Search for a song by song title and artist on Spotify and return the top results."""
        query = f"track:{song} artist:{artist}"
        results = self.sp.search(q=query, type='track', limit=limit)
        
        tracks = results['tracks']['items']
        if not tracks:
            print(f"No results found for: {song} by {artist}")
            return []

        return [(t['name'], t['artists'][0]['name'], t['external_urls']['spotify']) for t in tracks]

    def get_url_from_song(self, song: str, artist: str) -> Union[None, str]:
        """Search for a song by song title and artist on Spotify and return the top result's URL."""
        result = self.search_song_on_spotify(song, artist, limit=1)
        if result:
            if len(result) > 0:
                return result[0][2]
        raise Exception(f"Failed to find {song} by {artist} on Spotify")
    
    def get_embed_url(self, url: str) -> str:
        """Extract the track ID from the Spotify URL and generate the embed URL."""
        track_id = self.get_track_id(url)
        return f"https://open.spotify.com/embed/track/{track_id}"

    @staticmethod
    def get_youtube_url_from_song(song: str, artist: Optional[str] = None) -> str:
        """Search YouTube for the song and artist and return the video URL."""
        search_query = f"{song} by {artist} lyrics" if artist else song
        videos = VideosSearch(search_query, limit=5).result()['result']
        if not videos:
            raise ValueError(f"No YouTube results found for: {search_query}")
        video = videos[0]
        title, url = video['title'], video['link']
        print(f"YouTube Search: {search_query}\nYouTube Result: {title} ({url})\n")
        return url

    @property
    def youtube_url(self) -> str:
        """Lazy property for YouTube URL; calculates and stores the URL if not set."""
        if not self._youtube_url:
            self._youtube_url = self.get_youtube_url_from_song(self.song, self.artist)
        return self._youtube_url

    @property
    def youtube_song(self) -> str:
        """Lazy property for YouTube Song"""
        if self._youtube_song is None:
            self._youtube_song = YouTubeSong(self.youtube_url)
        return self._youtube_song

    @property
    def youtube_embed_url(self) -> str:
        """Lazy property for YouTube embed URL; initializes YouTube video object if not set."""
        self.youtube_song: YouTubeSong
        return self.youtube_song.embed_url

    def _download_audio(self, verbose: int = 0):
        """Download the audio by using the YouTubeSong class."""
        return self.youtube_song.download_audio(verbose=verbose)


class SpotifyPlaylist:
    
    ENTITY_TYPE = "playlist"
    
    def __init__(self, url: str):
        self.sp = self.authenticate()
        self.url = url
        self.spotipy_playlist = self.sp.playlist(self.playlist_id)
        self.title = self.get_title()
        self._songs = None
        self.filename = self.get_filename()
        self.audio = None
        self.audio_zipped = None
        self.length = self.get_num_tracks_spotify_playlist()
        self.thumbnail = self.get_thumbnail()
        self.current_batch_size = None
        self.platform = "Spotify"
        self.entity_type = SpotifyPlaylist.ENTITY_TYPE
        self.download_from = "YouTube"
        
    @staticmethod
    def is_url_valid(url: str) -> bool:
        return "spotify.com/playlist" in url

    def authenticate(self) -> spotipy.Spotify:
        return authenticate()

    @property
    def playlist_id(self) -> str:
        return self.url.split('/playlist/')[1].split('?')[0]

    @property
    def embed_url(self) -> str:
        return f"https://open.spotify.com/embed/playlist/{self.playlist_id}"

    @property
    def songs(self) -> List[SpotifySong]:
        if self._songs is None:
            self._songs = [
                SpotifySong(
                    song=track['track']['name'],
                    artist=track['track']['artists'][0]['name'],
                    url=track["track"]["external_urls"]["spotify"],
                ) for track in self.spotipy_playlist['tracks']['items']
            ]
        return self._songs

    def get_num_tracks_spotify_playlist(self) -> int:
        return self.spotipy_playlist["tracks"]["total"]

    def get_thumbnail(self) -> str:
        return self.spotipy_playlist["images"][0]["url"]

    def get_title(self) -> str:
        return self.spotipy_playlist["name"]

    def get_filename(self) -> str:
        """Generate a filename for the playlist zip file."""
        playlist_title = self.sp.playlist(self.url.split('/playlist/')[1].split('?')[0])['name']
        return f"{playlist_title}.zip"

    def download_audio(
        self,
        *,
        stqdm: bool = False,
        verbose: int = 0
    ) -> bytes:
        if not self.audio:
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
    
