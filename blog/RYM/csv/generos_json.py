import json
import requests
from time import sleep
from typing import Dict, List, Set
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import musicbrainzngs
import os
import sys
from datetime import datetime
import discogs_client
from dotenv import load_dotenv
import sqlite3

# Load environment variables
load_dotenv()

LASTFM_API_KEY = os.getenv('LASTFM_API_KEY')
LASTFM_USERNAME = os.getenv('LASTFM_USERNAME')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
DISCOGS_TOKEN = os.getenv('DISCOGS_TOKEN')

class GenreFetcher:
    def __init__(self, db_path='music_genres.db'):
        # API Setup
        self.lastfm_api_key = LASTFM_API_KEY
        
        credentials_manager = SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET
        )
        self.spotify = spotipy.Spotify(client_credentials_manager=credentials_manager)
        
        self.discogs = discogs_client.Client('GenreFetcher/1.0', user_token=DISCOGS_TOKEN)
        
        musicbrainzngs.set_useragent("MyMusicApp", "0.1", "your@email.com")
        
        # Cache setup
        self.cache = {}

        # Database setup
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                song_name TEXT,
                artist_name TEXT,
                artist_mbid TEXT,
                playcount INTEGER,
                period TEXT,
                year INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS genres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_id INTEGER,
                source TEXT,
                genre TEXT,
                FOREIGN KEY(song_id) REFERENCES songs(id)
            )
        ''')
        
        self.conn.commit()

    def get_lastfm_genres(self, artist: str) -> Set[str]:
        if not self.lastfm_api_key:
            return set()
            
        cache_key = f"lastfm_{artist}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist={artist}&api_key={self.lastfm_api_key}&format=json"
        try:
            response = requests.get(url)
            data = response.json()
            if 'artist' in data and 'tags' in data['artist'] and 'tag' in data['artist']['tags']:
                tags = {tag['name'].lower() for tag in data['artist']['tags']['tag']}
                self.cache[cache_key] = tags
                return tags
        except Exception as e:
            print(f"Error en Last.fm para {artist}: {str(e)}")
        return set()

    def get_spotify_genres(self, artist: str) -> Set[str]:
        cache_key = f"spotify_{artist}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        try:
            results = self.spotify.search(q=artist, type='artist', limit=1)
            if results['artists']['items']:
                genres = set(results['artists']['items'][0]['genres'])
                self.cache[cache_key] = genres
                return genres
        except Exception as e:
            print(f"Error en Spotify para {artist}: {str(e)}")
        return set()

    def get_musicbrainz_genres(self, mbid: str) -> Set[str]:
        if not mbid:
            return set()
            
        cache_key = f"mb_{mbid}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        try:
            result = musicbrainzngs.get_artist_by_id(mbid, includes=['tags'])
            if 'artist' in result and 'tag-list' in result['artist']:
                tags = {tag['name'].lower() for tag in result['artist']['tag-list']}
                self.cache[cache_key] = tags
                return tags
        except Exception as e:
            print(f"Error en MusicBrainz para {mbid}: {str(e)}")
        return set()

    def get_discogs_genres(self, album: str) -> Set[str]:
        cache_key = f"discogs_{album}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            results = self.discogs.search(album, type='release')
            if results and len(results) > 0:
                album_result = results[0]
                genres = set()

                if hasattr(album_result, 'genres') and album_result.genres:
                    genres.update(genre.lower() for genre in album_result.genres)

                if hasattr(album_result, 'styles') and album_result.styles:
                    genres.update(style.lower() for style in album_result.styles)

                self.cache[cache_key] = genres
                return genres
        except Exception as e:
            print(f"Error en Discogs para {album}: {str(e)}")
        return set()

    def process_songs(self, input_file: str, temp_file: str = None) -> Dict:
        # Load original data
        with open(input_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        if 'users' not in original_data:
            print("Error: JSON file does not have the expected structure")
            return None

        # Determine starting point and last processed details
        processed_users = set()
        last_processed_song_index = 0
        last_processed_username = None

        if temp_file and os.path.exists(temp_file):
            try:
                with open(temp_file, 'r', encoding='utf-8') as f:
                    temp_data = json.load(f)
                    
                    # More robust resume logic
                    if 'last_processed_username' in temp_data:
                        last_processed_username = temp_data['last_processed_username']
                        last_processed_song_index = temp_data.get('last_processed_song_index', 0)
                    
                    if 'users' in temp_data:
                        processed_users = set(temp_data['users'].keys())
                    
                    print(f"Resuming from temporary file. Already processed {len(processed_users)} users.")
            except Exception as e:
                print(f"Error reading temporary file: {e}")

        # Prepare database transaction
        cursor = self.conn.cursor()
        
        # Process each user and their songs
        total_users = len(original_data['users'])
        users_list = list(original_data['users'].items())
        
        # Find starting index if resuming from a specific user
        start_index = 0
        if last_processed_username:
            for i, (username, _) in enumerate(users_list):
                if username == last_processed_username:
                    start_index = i
                    break

        for current_user, (username, songs) in enumerate(users_list[start_index:], start_index):
            if username in processed_users:
                print(f"Skipping already processed user: {username}")
                continue

            print(f"\nProcessing user {current_user+1}/{total_users}: {username}")
            
            for song_index, song in enumerate(songs[last_processed_song_index:], last_processed_song_index):
                print(f"\nProcessing song {song_index+1}/{len(songs)}: {song['name']} - {song['artist']['name']}")
                
                # Fetch genres
                artist_name = song['artist']['name']
                artist_mbid = song['artist'].get('mbid', '')
                
                genres_by_source = {
                    'lastfm': list(self.get_lastfm_genres(artist_name)),
                    'spotify': list(self.get_spotify_genres(artist_name)),
                    'musicbrainz': list(self.get_musicbrainz_genres(artist_mbid)) if artist_mbid else [],
                    'discogs': list(self.get_discogs_genres(artist_name))
                }
                
                # Combine genres
                all_genres = set()
                for source_genres in genres_by_source.values():
                    all_genres.update(source_genres)
                
                # Prepare song data for database
                cursor.execute('''
                    INSERT INTO songs 
                    (username, song_name, artist_name, artist_mbid, playcount, period, year) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    username, 
                    song['name'], 
                    artist_name, 
                    artist_mbid, 
                    song.get('playcount', 0), 
                    original_data['period'], 
                    original_data['year']
                ))
                song_id = cursor.lastrowid

                # Insert genres
                for source, genres in genres_by_source.items():
                    for genre in genres:
                        cursor.execute('''
                            INSERT INTO genres (song_id, source, genre) 
                            VALUES (?, ?, ?)
                        ''', (song_id, source, genre))
                
                # Print genres found
                print("\nGenres found by source:")
                for source, genres in genres_by_source.items():
                    print(f"  {source.upper()}: {', '.join(genres) if genres else 'None'}")
                print("  ------------------------")
                
                # Commit every 10 songs and save progress
                if (song_index + 1) % 10 == 0:
                    self.conn.commit()
                    temp_progress = {
                        'period': original_data['period'],
                        'year': original_data['year'],
                        'last_processed_username': username,
                        'last_processed_song_index': song_index + 1
                    }
                    with open(f"{input_file}_enriched_temp.json", 'w', encoding='utf-8') as f:
                        json.dump(temp_progress, f, ensure_ascii=False, indent=2)
                
                # Rate limiting
                sleep(1)
            
            # Reset last processed song index for subsequent users
            last_processed_song_index = 0
            
            # Final commit for this user
            self.conn.commit()
        
        print("\nProcessing complete. Data saved to SQLite database.")
        return {"status": "completed"}

    def __del__(self):
        # Ensure database connection is closed
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py original_file.json [temp_file.json]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    temp_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    fetcher = GenreFetcher()
    result = fetcher.process_songs(input_file, temp_file)
    
    if result:
        print("Process completed successfully.")
    else:
        print("Error processing the file.")

if __name__ == "__main__":
    main()