from typing import Optional, Union, Tuple, List, Dict
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from youtubesearchpython import VideosSearch
from dotenv import load_dotenv
import re

from music_downloader.base import BaseSong, BasePlaylist
from music_downloader.youtube import YouTubeSong


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

    @staticmethod
    def is_url_valid(url: str) -> bool:
        return "spotify.com/track" in url

    def scrape_song_info(self) -> Dict[str, str]:
        song, artist = self.get_song_details_from_spotify(self.url)
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
            self._youtube_url = self.get_youtube_url_from_song(self.title, self.artist)
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


class SpotifyPlaylist(BasePlaylist):
    
    def __init__(self, url: str):
        self.sp = self.authenticate()
        super().__init__(url)

    def authenticate(self) -> spotipy.Spotify:
        return authenticate()

    @staticmethod
    def get_platform() -> str:
        return "Spotify"
    
    @staticmethod
    def get_download_platform() -> str:
        return "YouTube"

    @staticmethod
    def is_url_valid(url: str) -> bool:
        return "spotify.com/playlist" in url

    @property
    def playlist_id(self) -> str:
        return self.url.split('/playlist/')[1].split('?')[0]

    @staticmethod
    def get_embed_url(playlist_id: str) -> str:
        return f"https://open.spotify.com/embed/playlist/{playlist_id}"

    def scrape_playlist_info(self) -> Dict[str, Union[str, None]]:
        info = self.sp.playlist(self.playlist_id)
        info["title"] = info["name"]
        info["curator"] = info['owner']['id']
        info["embed_url"] = self.get_embed_url(self.playlist_id)
        return info

    @staticmethod
    def create_song(*, song: str, artist: str, url: str) -> SpotifySong:
        return SpotifySong(song=song, artist=artist, url=url)

    @property
    def songs(self) -> List[SpotifySong]:
        if self._songs is None:
            self._songs = [
                self.create_song(
                    song=track['track']['name'],
                    artist=track['track']['artists'][0]['name'],
                    url=track["track"]["external_urls"]["spotify"],
                ) for track in self.info['tracks']['items']
            ]
        return self._songs
    
    def get_num_tracks(self, ignore_limit: bool = False) -> int:
        num_tracks = self.info["tracks"]["total"]
        if ignore_limit:
            return min(num_tracks, 100)
        return num_tracks

    def thumbnail(self) -> str:
        return self.info["images"][0]["url"]