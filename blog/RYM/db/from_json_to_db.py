import json
import sqlite3
from datetime import datetime
import logging
import sys
from pathlib import Path
import time

class LastFMDatabaseMigrator:
    def __init__(self, db_path, checkpoint_path):
        self.db_path = db_path
        self.checkpoint_path = Path(checkpoint_path)
        
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
        
    def setup_database(self):
        """Crear las tablas si no existen"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL
                );

                CREATE TABLE IF NOT EXISTS artists (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    mbid TEXT
                );

                CREATE TABLE IF NOT EXISTS albums (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    artist_id INTEGER,
                    mbid TEXT,
                    image_url TEXT,
                    FOREIGN KEY (artist_id) REFERENCES artists(id),
                    UNIQUE(name, artist_id)
                );

                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    artist_id INTEGER,
                    album_id INTEGER,
                    mbid TEXT,
                    duration INTEGER,
                    url TEXT,
                    FOREIGN KEY (artist_id) REFERENCES artists(id),
                    FOREIGN KEY (album_id) REFERENCES albums(id),
                    UNIQUE(name, artist_id, album_id)
                );

                CREATE TABLE IF NOT EXISTS plays (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    track_id INTEGER,
                    timestamp INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (track_id) REFERENCES tracks(id),
                    UNIQUE(user_id, track_id, timestamp)
                );

                CREATE TABLE IF NOT EXISTS genres (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL
                );

                CREATE TABLE IF NOT EXISTS track_genres (
                    track_id INTEGER,
                    genre_id INTEGER,
                    PRIMARY KEY (track_id, genre_id),
                    FOREIGN KEY (track_id) REFERENCES tracks(id),
                    FOREIGN KEY (genre_id) REFERENCES genres(id)
                );
            """)

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

    def get_or_create_record(self, conn, table, search_params, insert_params=None):
        """Obtener o crear un registro en la base de datos"""
        if insert_params is None:
            insert_params = search_params

        # Construir la consulta SELECT
        where_clause = ' AND '.join(f'{k} = ?' for k in search_params.keys())
        select_query = f'SELECT id FROM {table} WHERE {where_clause}'
        
        cursor = conn.execute(select_query, list(search_params.values()))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Si no existe, crear nuevo registro
        columns = ', '.join(insert_params.keys())
        placeholders = ', '.join('?' * len(insert_params))
        insert_query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
        
        cursor = conn.execute(insert_query, list(insert_params.values()))
        return cursor.lastrowid

    def process_json_file(self, json_path):
        """Procesar el archivo JSON y migrar los datos"""
        self.logger.info(f"Iniciando procesamiento de {json_path}")
        
        # Cargar el último checkpoint
        checkpoint = self.load_checkpoint()
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            
            for username, tracks in data['users'].items():
                # Verificar si debemos saltar este usuario según el checkpoint
                if checkpoint['last_user'] and username <= checkpoint['last_user']:
                    continue
                
                self.logger.info(f"Procesando usuario: {username}")
                
                try:
                    # Crear o obtener usuario
                    user_id = self.get_or_create_record(
                        conn, 
                        'users', 
                        {'username': username}
                    )
                    
                    for track in tracks:
                        # Procesar solo timestamps posteriores al último checkpoint
                        for timestamp in track['timestamps']:
                            if checkpoint['last_timestamp'] and timestamp <= checkpoint['last_timestamp']:
                                continue
                                
                            try:
                                # Crear o obtener artista
                                artist_id = self.get_or_create_record(
                                    conn,
                                    'artists',
                                    {'name': track['artist']['name']},
                                    {
                                        'name': track['artist']['name'],
                                        'mbid': track['artist']['mbid']
                                    }
                                )
                                
                                # Crear o obtener álbum si existe
                                album_id = None
                                if 'album' in track and track['album']:
                                    album_id = self.get_or_create_record(
                                        conn,
                                        'albums',
                                        {'name': track['album']['name'], 'artist_id': artist_id},
                                        {
                                            'name': track['album']['name'],
                                            'artist_id': artist_id,
                                            'mbid': track['album']['mbid'],
                                            'image_url': track['album'].get('image')
                                        }
                                    )
                                
                                # Crear o obtener track
                                track_id = self.get_or_create_record(
                                    conn,
                                    'tracks',
                                    {
                                        'name': track['name'],
                                        'artist_id': artist_id,
                                        'album_id': album_id
                                    },
                                    {
                                        'name': track['name'],
                                        'artist_id': artist_id,
                                        'album_id': album_id,
                                        'mbid': track['mbid'],
                                        'duration': track['duration'],
                                        'url': track['url']
                                    }
                                )
                                
                                # Registrar reproducción
                                conn.execute(
                                    """
                                    INSERT OR IGNORE INTO plays (user_id, track_id, timestamp)
                                    VALUES (?, ?, ?)
                                    """,
                                    (user_id, track_id, timestamp)
                                )
                                
                                # Guardar checkpoint periódicamente
                                self.save_checkpoint(username, timestamp)
                                
                            except Exception as e:
                                self.logger.error(f"Error procesando track: {track['name']} - {str(e)}")
                                continue
                            
                    conn.commit()
                    
                except Exception as e:
                    self.logger.error(f"Error procesando usuario {username}: {str(e)}")
                    conn.rollback()
                    continue
                
        self.logger.info("Migración completada exitosamente")

def main():
    # Configurar rutas
    db_path = sys.argv[1]
    checkpoint_path = 'migration_checkpoint.json'
    json_path = sys.argv[2]  # Ajusta según necesidad
    
    # Crear instancia del migrador
    migrator = LastFMDatabaseMigrator(db_path, checkpoint_path)
    
    # Configurar base de datos
    migrator.setup_database()
    
    # Ejecutar migración
    migrator.process_json_file(json_path)

if __name__ == "__main__":
    main()