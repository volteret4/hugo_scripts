import json
import sqlite3
import logging
import sys
from pathlib import Path
import time
from datetime import datetime
import requests
from urllib.parse import quote
import base64
import os
import musicbrainzngs as mb
from dotenv import load_dotenv

load_dotenv()

class LastFMDatabaseLoader:
    def __init__(self, db_path, checkpoint_path, schema_path):
        self.db_path = db_path
        self.checkpoint_path = Path(checkpoint_path)
        self.schema_path = schema_path
        
        # Configurar APIs
        self.setup_apis()
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('migration.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_apis(self):
        """Configurar las APIs necesarias"""
        # Last.fm
        self.lastfm_api_key = os.getenv('LASTFM_API_KEY')
        
        # Spotify
        self.spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.spotify_token = self.get_spotify_token()
        
        # MusicBrainz
        mb.set_useragent(
            "MusicLibraryEnricher",
            "1.0",
            os.getenv('CONTACT_EMAIL', 'your@email.com')
        )
        
        # Discogs
        self.discogs_token = os.getenv('DISCOGS_TOKEN')

    def setup_database(self):
        """Crear el esquema de la base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            with open(self.schema_path, 'r') as schema_file:
                conn.executescript(schema_file.read())
            self.logger.info("Base de datos inicializada correctamente")

    def get_spotify_token(self):
        """Obtener token de Spotify"""
        if not (self.spotify_client_id and self.spotify_client_secret):
            return None
            
        auth_string = f"{self.spotify_client_id}:{self.spotify_client_secret}"
        auth_bytes = auth_string.encode('utf-8')
        auth_base64 = str(base64.b64encode(auth_bytes), 'utf-8')
        
        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        
        try:
            response = requests.post(url, headers=headers, data=data)
            json_result = response.json()
            return json_result.get("access_token")
        except Exception as e:
            self.logger.error(f"Error obteniendo token de Spotify: {str(e)}")
            return None

    def get_genres_from_apis(self, artist_name, track_name, mbid):
        """Obtener géneros de todas las APIs disponibles"""
        genres = []
        
        # Last.fm
        if self.lastfm_api_key:
            url = f"http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={self.lastfm_api_key}&artist={quote(artist_name)}&track={quote(track_name)}&format=json"
            try:
                response = requests.get(url)
                data = response.json()
                if 'track' in data and 'toptags' in data['track']:
                    for tag in data['track']['toptags']['tag']:
                        genres.append(('lastfm', tag['name']))
            except Exception as e:
                self.logger.error(f"Error con Last.fm API: {str(e)}")

        # Spotify
        if self.spotify_token:
            headers = {"Authorization": f"Bearer {self.spotify_token}"}
            search_url = f"https://api.spotify.com/v1/search?q=track:{quote(track_name)}+artist:{quote(artist_name)}&type=track&limit=1"
            try:
                response = requests.get(search_url, headers=headers)
                data = response.json()
                if 'tracks' in data and 'items' in data['tracks'] and data['tracks']['items']:
                    track = data['tracks']['items'][0]
                    artist_id = track['artists'][0]['id']
                    artist_url = f"https://api.spotify.com/v1/artists/{artist_id}"
                    artist_response = requests.get(artist_url, headers=headers)
                    artist_data = artist_response.json()
                    for genre in artist_data.get('genres', []):
                        genres.append(('spotify', genre))
            except Exception as e:
                self.logger.error(f"Error con Spotify API: {str(e)}")

        # MusicBrainz
        if mbid:
            try:
                result = mb.get_recording_by_id(mbid, includes=['tags'])
                for tag in result['recording'].get('tag-list', []):
                    genres.append(('musicbrainz', tag['name']))
                    sleep = random.uniform(0.1, 0.5)
                    time.sleep(sleep)
            except Exception as e:
                self.logger.error(f"Error con MusicBrainz API: {str(e)}")

        # Discogs
        if self.discogs_token:
            headers = {'Authorization': f'Discogs token={self.discogs_token}'}
            search_url = f"https://api.discogs.com/database/search?q={quote(f'{artist_name} {track_name}')}&type=release"
            try:
                response = requests.get(search_url, headers=headers)
                data = response.json()
                if 'results' in data and data['results']:
                    result = data['results'][0]
                    for genre in result.get('genre', []):
                        genres.append(('discogs_genre', genre))
                    for style in result.get('style', []):
                        genres.append(('discogs_style', style))
            except Exception as e:
                self.logger.error(f"Error con Discogs API: {str(e)}")

        return genres

    def parse_timestamp(self, timestamp):
        """Convertir timestamp a componentes de tiempo"""
        dt = datetime.fromtimestamp(timestamp)
        return {
            'timestamp': timestamp,
            'year': dt.year,
            'month': dt.month,
            'day': dt.day,
            'hour': dt.hour
        }

    def update_user_stats(self, conn, user_id, track_id, artist_id, album_id, genres, timestamp):
        """Actualizar estadísticas de usuario"""
        tables = [
            ('user_track_stats', 'track_id', track_id),
            ('user_artist_stats', 'artist_id', artist_id),
        ]
        
        if album_id:
            tables.append(('user_album_stats', 'album_id', album_id))

        for table, id_column, id_value in tables:
            conn.execute(f"""
                INSERT INTO {table} (user_id, {id_column}, play_count, first_played, last_played)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(user_id, {id_column}) DO UPDATE SET
                    play_count = play_count + 1,
                    first_played = MIN(first_played, excluded.first_played),
                    last_played = MAX(last_played, excluded.last_played)
            """, (user_id, id_value, timestamp, timestamp))

        # Actualizar estadísticas de géneros
        for genre_id in genres:
            conn.execute("""
                INSERT INTO user_genre_stats (user_id, genre_id, play_count, first_played, last_played)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(user_id, genre_id) DO UPDATE SET
                    play_count = play_count + 1,
                    first_played = MIN(first_played, excluded.first_played),
                    last_played = MAX(last_played, excluded.last_played)
            """, (user_id, genre_id, timestamp, timestamp))

    def process_track(self, conn, track_data, user_id, timestamp):
        """Procesar una pista y sus relaciones"""
        try:
            # Insertar artista
            artist_id = self.get_or_create_record(
                conn,
                'artists',
                {'name': track_data['artist']['name']},
                {
                    'name': track_data['artist']['name'],
                    'mbid': track_data['artist']['mbid']
                }
            )

            # Insertar álbum si existe
            album_id = None
            if 'album' in track_data and track_data['album']:
                album_id = self.get_or_create_record(
                    conn,
                    'albums',
                    {'name': track_data['album']['name'], 'artist_id': artist_id},
                    {
                        'name': track_data['album']['name'],
                        'artist_id': artist_id,
                        'mbid': track_data['album'].get('mbid'),
                        'image_url': track_data['album'].get('image')
                    }
                )

            # Insertar track
            track_id = self.get_or_create_record(
                conn,
                'tracks',
                {
                    'name': track_data['name'],
                    'artist_id': artist_id,
                    'album_id': album_id
                },
                {
                    'name': track_data['name'],
                    'artist_id': artist_id,
                    'album_id': album_id,
                    'mbid': track_data.get('mbid'),
                    'duration': track_data.get('duration'),
                    'url': track_data.get('url')
                }
            )

            # Obtener y procesar géneros
            genres = self.get_genres_from_apis(
                track_data['artist']['name'],
                track_data['name'],
                track_data.get('mbid')
            )
            
            genre_ids = []
            for source, genre_name in genres:
                genre_id = self.get_or_create_record(
                    conn,
                    'genres',
                    {'name': genre_name, 'source_id': self.get_source_id(conn, source)},
                    {'name': genre_name, 'source_id': self.get_source_id(conn, source)}
                )
                genre_ids.append(genre_id)
                
                # Asociar género con track
                conn.execute("""
                    INSERT OR IGNORE INTO track_genres (track_id, genre_id, confidence)
                    VALUES (?, ?, 1.0)
                """, (track_id, genre_id))

            # Registrar reproducción
            time_data = self.parse_timestamp(timestamp)
            conn.execute("""
                INSERT INTO user_plays (
                    user_id, track_id, timestamp, year, month, day, hour
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, track_id,
                time_data['timestamp'], time_data['year'],
                time_data['month'], time_data['day'],
                time_data['hour']
            ))

            # Actualizar estadísticas
            self.update_user_stats(conn, user_id, track_id, artist_id, album_id, genre_ids, timestamp)

            return track_id

        except Exception as e:
            self.logger.error(f"Error procesando track {track_data['name']}: {str(e)}")
            return None

    def get_source_id(self, conn, source_name):
        """Obtener ID de la fuente de géneros"""
        cursor = conn.execute(
            "SELECT id FROM genre_sources WHERE name = ?",
            (source_name,)
        )
        result = cursor.fetchone()
        return result[0] if result else None

    def get_or_create_record(self, conn, table, search_params, insert_params=None):
        """Obtener o crear un registro en la base de datos"""
        if insert_params is None:
            insert_params = search_params

        where_clause = ' AND '.join(f'{k} = ?' for k in search_params.keys())
        select_query = f'SELECT id FROM {table} WHERE {where_clause}'
        
        cursor = conn.execute(select_query, list(search_params.values()))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        columns = ', '.join(insert_params.keys())
        placeholders = ', '.join('?' * len(insert_params))
        insert_query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
        
        cursor = conn.execute(insert_query, list(insert_params.values()))
        return cursor.lastrowid

    def load_checkpoint(self):
        """Cargar el último checkpoint procesado"""
        if self.checkpoint_path.exists():
            with open(self.checkpoint_path, 'r') as f:
                return json.load(f)
        return {'last_user': None, 'last_timestamp': None}

    def save_checkpoint(self, username, timestamp):
        """Guardar el progreso actual"""
        checkpoint = {'last_user': username, 'last_timestamp': timestamp}
        with open(self.checkpoint_path, 'w') as f:
            json.dump(checkpoint, f)

    def process_json_file(self, json_path):
        """Procesar archivo JSON y migrar datos"""
        self.logger.info(f"Iniciando procesamiento de {json_path}")
        
        checkpoint = self.load_checkpoint()
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            
            for username, tracks in data['users'].items():
                if checkpoint['last_user'] and username <= checkpoint['last_user']:
                    continue
                
                self.logger.info(f"Procesando usuario: {username}")
                
                try:
                    user_id = self.get_or_create_record(
                        conn, 
                        'users', 
                        {'username': username}
                    )
                    
                    for track in tracks:
                        for timestamp in track['timestamps']:
                            if checkpoint['last_timestamp'] and timestamp <= checkpoint['last_timestamp']:
                                continue
                            
                            self.process_track(conn, track, user_id, timestamp)
                            self.save_checkpoint(username, timestamp)
                    
                    conn.commit()
                    
                except Exception as e:
                    self.logger.error(f"Error procesando usuario {username}: {str(e)}")
                    conn.rollback()
                    continue
        
        self.logger.info("Migración completada exitosamente")

def main():
    if len(sys.argv) != 3:
        print("Uso: python script.py <database_path> <json_path>")
        sys.exit(1)

    database_path = sys.argv[1]
    json_path = sys.argv[2]
    schema_path = "schema.sql"  # El archivo schema.sql debe estar en el mismo directorio
    checkpoint_path = "checkpoint.json"

    # Verificar si la base de datos está inicializada
    loader = LastFMDatabaseLoader(database_path, checkpoint_path, schema_path)

    if not Path(database_path).exists():
        loader.logger.info("La base de datos no existe. Creándola...")
        loader.setup_database()

    # Procesar el archivo JSON
    loader.process_json_file(json_path)

if __name__ == "__main__":
    main()