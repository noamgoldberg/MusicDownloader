from typing import Optional, Union, Tuple, List
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from youtubesearchpython import VideosSearch
from dotenv import load_dotenv
from io import BytesIO
from stqdm import stqdm as st_tqdm
import re

from music_downloader.youtube import YouTubeVideo
from utils.zip_utils import zip_audio_files


load_dotenv()

def authenticate_spotify(
    spotify_client_id: Optional[str] = None,
    spotify_client_secret: Optional[str] = None,
    spotify_redirect_uri: Optional[str] = None,
) -> spotipy.Spotify:
    """Authenticate Spotify API connection"""
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=spotify_client_id or os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=spotify_client_secret or os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=spotify_redirect_uri or os.getenv("SPOTIFY_REDIRECT_URI"),
            scope="playlist-read-private"
        )
    )

class SpotifySong:
    
    URL_FUNC = lambda url: "spotify.com/track" in url
    ENTITY_TYPE = "song"
    
    def __init__(
        self,
        url: Optional[str] = None,
        song: Optional[str] = None,
        artist: Optional[str] = None,
        spotify_client_id: Optional[str] = None,
        spotify_client_secret: Optional[str] = None,
        spotify_redirect_uri: Optional[str] = None,
    ):
        if not (url or (song and artist)):
            raise Exception(f"{url=}, {song=}, {artist=}: Must provide either URL or Song & Artist to instantiate SpotifySong")
        self.sp = self.authenticate(
            spotify_client_id=spotify_client_id,
            spotify_client_secret=spotify_client_secret,
            spotify_redirect_uri=spotify_redirect_uri,
        )
        self._youtube_url = None  # Internal variable to store the YouTube URL
        if url:
            self.spotify_url = url
        else:
            self.spotify_url = self.get_spotify_url_from_song(song, artist)
        self.song, self.artist = self.get_song_details_from_spotify(self.spotify_url)
        self._validate_details(song, artist)
        self.title = f"{self.song} by {self.artist}"
        self.spotify_embed_url = self.get_spotify_embed_url(self.spotify_url)
        self._youtube_url = None
        self._youtube_video = None
        self._youtube_embed_url = None
        self.platform = "Spotify"
        self.entity_type = SpotifySong.ENTITY_TYPE
        self.download_from = "YouTube"

    def _validate_details(self, song: str, artist: str):
        for (param, value) in [("song", song), ("artist", artist)]:
            if value and value.strip().lower() != getattr(self, param, "").strip().lower():
                raise ValueError(f"Given {param} {value} does not match {param} extracted from given url, '{getattr(self, param)}'")

    @property
    def spotify_track_id(self) -> str:
        return re.search(r"track/([a-zA-Z0-9]+)", self.spotify_url).group(1)

    def authenticate(
        self,
        spotify_client_id: Optional[str] = None,
        spotify_client_secret: Optional[str] = None,
        spotify_redirect_uri: Optional[str] = None,
    ) -> spotipy.Spotify:
        return authenticate_spotify(
            spotify_client_id=spotify_client_id,
            spotify_client_secret=spotify_client_secret,
            spotify_redirect_uri=spotify_redirect_uri,
        )

    def get_song_details_from_spotify(self, spotify_url: str) -> tuple:
        """Get song name and artist from Spotify URL."""
        track = self.sp.track(spotify_url)
        song_name = track['name']
        artist_name = track['artists'][0]['name']
        print(f"Retrieved from Spotify: {song_name} by {artist_name}")
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

    def get_spotify_url_from_song(self, song: str, artist: str) -> Union[None, str]:
        """Search for a song by song title and artist on Spotify and return the top result's URL."""
        result = self.search_song_on_spotify(song, artist, limit=1)
        if result:
            if len(result) > 0:
                return result[0][2]
        raise Exception(f"Failed to find {song} by {artist} on Spotify")

    def get_youtube_url_from_song(self, song: str, artist: Optional[str] = None) -> str:
        """Search YouTube for the song and artist and return the video URL."""
        search_query = f"{song} by {artist} lyrics" if artist else song
        videos = VideosSearch(search_query, limit=5).result()['result']
        if not videos:
            raise ValueError(f"No YouTube results found for: {search_query}")
        video = videos[0]
        title, url = video['title'], video['link']
        print(f"YouTube Search: {search_query}\nYouTube Result: {title} ({url})\n")
        return url

    def get_spotify_embed_url(self, spotify_url: str) -> str:
        """Extract the track ID from the Spotify URL and generate the embed URL."""
        track_id = spotify_url.split("/track/")[1].split("?")[0]
        spotify_embed_url = f"https://open.spotify.com/embed/track/{track_id}"
        return spotify_embed_url

    @property
    def youtube_url(self) -> str:
        """Lazy property for YouTube URL; calculates and stores the URL if not set."""
        if not self._youtube_url:
            self._youtube_url = self.get_youtube_url_from_song(self.song, self.artist)
        return self._youtube_url

    @property
    def youtube_video(self) -> str:
        """Lazy property for YouTube Video"""
        if self._youtube_video is None:
            self._youtube_video = YouTubeVideo(self.youtube_url)
        return self._youtube_video

    @property
    def youtube_embed_url(self) -> str:
        """Lazy property for YouTube embed URL; initializes YouTube video object if not set."""
        if not self.youtube_video:
            self.youtube_video = YouTubeVideo(self.youtube_url)
        return self.youtube_video.embed_url

    @property
    def filename(self) -> str:
        """Return the filename for the audio."""
        return f"{self.song} by {self.artist}.mp3"

    def download_audio(self, verbose: int = 0):
        """Download the audio by using the YouTubeVideo class."""
        if not self.youtube_video:
            self.youtube_video = YouTubeVideo(self.youtube_url)
        return self.youtube_video.download_audio(verbose=verbose)

    @property
    def _audio(self) -> Union[BytesIO, None]:
        if not self.youtube_video:
            return None
        return self.youtube_video._audio

    @property
    def audio(self) -> Union[BytesIO, None]:
        return self._audio


class SpotifyPlaylist:
    
    URL_FUNC = lambda url: "spotify.com/playlist" in url
    ENTITY_TYPE = "playlist"
    
    def __init__(
        self,
        url: str,
        spotify_client_id: Optional[str] = None,
        spotify_client_secret: Optional[str] = None,
        spotify_redirect_uri: Optional[str] = None,
    ):
        self.sp = self.authenticate(
            spotify_client_id=spotify_client_id,
            spotify_client_secret=spotify_client_secret,
            spotify_redirect_uri=spotify_redirect_uri,
        )
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
    
    def authenticate(
        self,
        spotify_client_id: Optional[str] = None,
        spotify_client_secret: Optional[str] = None,
        spotify_redirect_uri: Optional[str] = None,
    ) -> spotipy.Spotify:
        return authenticate_spotify(
            spotify_client_id=spotify_client_id,
            spotify_client_secret=spotify_client_secret,
            spotify_redirect_uri=spotify_redirect_uri,
        )
        
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
        return f"{playlist_title.replace(' ', '_')}.zip"

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
    
