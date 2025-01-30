
#!/usr/bin/env python
#
# Script Name: .py
# Description: 
# Author: volteret4
# Repository: https://github.com/volteret4/
# License:
# TODO: 
# Notes:
#   Dependencies:  - python3, 
#   python script.py --api-key TU_API_KEY --users usuario1 usuario2 --year 2023
#   python script.py --api-key TU_API_KEY --users usuario1 usuario2 usuario3 --find-coincidences

from typing import Optional
from pathlib import Path
import json
import csv
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Tuple, Set
import os
from collections import defaultdict
import statistics
import argparse
from itertools import combinations
from dotenv import load_dotenv
import sys

load_dotenv()

# Tu API key de Last.fm
API_KEY = os.getenv('LASTFM_API_KEY')


# Lista de usuarios que quieres analizar
USUARIOS = [
    "alberto_gu",
    "BipolarMuzik",
    "bloodinmyhand",
    "EliasJ72",
    "Frikomid",
    "GabredMared",
    "Lonsonxd",
    "Mister_Dimentio",
    "Music-is-Crap",
    "Nubis84",
    "paqueradejere",
    "Rocky_stereo",
    "sdecandelario"
]

AÑO = sys.argv[1]

class DataManager:
    def __init__(self, base_dir: str = 'data'):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_storage_path(self, data_type: str, **kwargs) -> Path:
        """
        Genera una ruta de almacenamiento única basada en el tipo de datos y parámetros
        
        data_type: 'user_data', 'year_data', 'coincidences'
        kwargs: parámetros específicos (username, year, etc.)
        """
        if data_type == 'user_data':
            return self.base_dir / 'users' / kwargs['username']
        elif data_type == 'year_data':
            return self.base_dir / 'years' / str(kwargs['year']) / kwargs['username']
        elif data_type == 'coincidences':
            users = sorted(kwargs['users'])
            return self.base_dir / 'coincidences' / '+'.join(users)
        else:
            raise ValueError(f"Tipo de datos no soportado: {data_type}")

    def should_update(self, filepath: Path, update_interval: timedelta) -> bool:
        """Determina si los datos necesitan actualizarse basado en su antigüedad"""
        if not filepath.exists():
            return True
        
        file_time = datetime.fromtimestamp(filepath.stat().st_mtime)
        return datetime.now() - file_time > update_interval

    def save_data(self, data: Dict, data_type: str, **kwargs):
        """Guarda los datos con estructura de directorios organizada"""
        storage_path = self.get_storage_path(data_type, **kwargs)
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Añadir metadatos
        data['_metadata'] = {
            'type': data_type,
            'timestamp': datetime.now().isoformat(),
            'parameters': kwargs
        }
        
        with open(storage_path / 'data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_data(self, data_type: str, **kwargs) -> Optional[Dict]:
        """Carga datos si existen"""
        storage_path = self.get_storage_path(data_type, **kwargs)
        data_file = storage_path / 'data.json'
        
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None


class LastFMDataCollector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.data_manager = DataManager()
        self.base_url = "http://ws.audioscrobbler.com/2.0/"
        self.period_limits = {
            'weekly': 50,
            'monthly': 300,
            '12month': 1000
        }
        self.genre_limits = {
            'weekly': 25,
            'monthly': 50,
            '12month': 100
        }
    
    def _make_request(self, method: str, params: Dict) -> Dict:
        """Método helper para hacer peticiones a la API"""
        base_params = {
            'method': method,
            'api_key': self.api_key,
            'format': 'json'
        }
        params.update(base_params)
        
        response = requests.get(self.base_url, params=params)
        if response.status_code != 200:
            raise Exception(f"Error en la API: {response.status_code}")
        return response.json()



    def get_user_top_tracks(self, username: str, period: str) -> Dict:
        """Obtiene los top tracks de un usuario"""
        return self._make_request('user.gettoptracks', {
            'user': username,
            'period': period,
            'limit': self.period_limits[period]
        })

    def get_user_top_artists(self, username: str, period: str) -> Dict:
        """Obtiene los top artistas de un usuario"""
        return self._make_request('user.gettopartists', {
            'user': username,
            'period': period,
            'limit': self.period_limits[period]
        })

    def get_user_top_albums(self, username: str, period: str) -> Dict:
        """Obtiene los top álbumes de un usuario"""
        return self._make_request('user.gettopalbums', {
            'user': username,
            'period': period,
            'limit': self.period_limits[period]
        })

    def get_artist_tags(self, artist_name: str) -> List[str]:
        """Obtiene los tags (géneros) de un artista"""
        response = self._make_request('artist.gettoptags', {
            'artist': artist_name
        })
        return [tag['name'] for tag in response.get('toptags', {}).get('tag', [])]

    def get_recent_tracks(self, username: str, from_timestamp: int = None) -> Dict:
        """Obtiene el historial reciente de tracks"""
        params = {
            'user': username,
            'limit': 200  # Máximo permitido por la API
        }
        if from_timestamp:
            params['from'] = from_timestamp
        
        return self._make_request('user.getrecenttracks', params)

    def analyze_obsessions(self, data: Dict, period: str) -> Dict:
        """Analiza patrones de escucha obsesivos"""
        plays = defaultdict(lambda: {'count': 0, 'type': '', 'name': ''})
        
        for item_type in ['tracks', 'artists', 'albums']:
            items = data.get(f'top{item_type}', {}).get(item_type, [])
            counts = [int(item['playcount']) for item in items if 'playcount' in item]
            
            if counts:
                mean = statistics.mean(counts)
                std_dev = statistics.stdev(counts)
                threshold = mean + (2 * std_dev)  # 2 desviaciones estándar por encima de la media
                
                for item in items:
                    count = int(item.get('playcount', 0))
                    if count > threshold:
                        key = f"{item_type}_{item.get('name', '')}"
                        plays[key] = {
                            'count': count,
                            'type': item_type,
                            'name': item.get('name', ''),
                            'artist': item.get('artist', {}).get('name', '') if item_type != 'artists' else None,
                            'deviation_from_mean': (count - mean) / std_dev
                        }
        
        return dict(plays)

    def find_unique_coincidences(self, users: List[str], year: Optional[int] = None):
        """Encuentra coincidencias únicas entre usuarios"""
        # Intentar cargar coincidencias existentes
        existing_data = self.data_manager.load_data(
            'coincidences',
            users=users,
            year=year
        )
        
        update_interval = timedelta(days=1)
        storage_path = self.data_manager.get_storage_path(
            'coincidences',
            users=users,
            year=year
        )
        
        if existing_data and not self.data_manager.should_update(
            storage_path / 'data.json',
            update_interval
        ):
            print("Usando coincidencias existentes")
            return existing_data
        
        # Si no hay datos o necesitan actualización, procesar
        users_data = {}
        for username in users:
            if year:
                data = self.process_year(username, year)
            else:
                data = self.process_user(username)
            users_data[username] = data
        
        coincidences = self._calculate_coincidences(users_data)
        
        # Guardar coincidencias
        self.data_manager.save_data(
            coincidences,
            'coincidences',
            users=users,
            year=year
        )
        return coincidences

    def save_data(self, username: str, period: str, data: Dict):
        """Guarda los datos en formato JSON y actualiza el timestamp"""
        timestamp = int(datetime.now().timestamp())
        
        # Crear directorio si no existe
        os.makedirs(f'data/{username}', exist_ok=True)
        
        # Guardar datos
        filename = f'data/{username}/{period}_{timestamp}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Actualizar timestamp
        self._save_timestamp(username, timestamp)

    def _save_timestamp(self, username: str, timestamp: int):
        """Guarda el último timestamp procesado"""
        filename = f'data/{username}/last_update.txt'
        with open(filename, 'w') as f:
            f.write(str(timestamp))

    def _get_last_timestamp(self, username: str) -> int:
        """Obtiene el último timestamp procesado"""
        filename = f'data/{username}/last_update.txt'
        try:
            with open(filename, 'r') as f:
                return int(f.read().strip())
        except FileNotFoundError:
            return None

    def process_user(self, username: str):
        """Procesa todos los datos de un usuario"""
        last_timestamp = self._get_last_timestamp(username)
        data = {
            'timestamp': int(datetime.now().timestamp()),
            'username': username
        }
        
        # Recopilar datos para cada período
        for period in ['weekly', 'monthly', '12month']:
            period_data = {
                'top_tracks': self.get_user_top_tracks(username, period),
                'top_artists': self.get_user_top_artists(username, period),
                'top_albums': self.get_user_top_albums(username, period),
            }
            
            # Recopilar géneros
            genres = defaultdict(int)
            for artist in period_data['top_artists']['topartists']['artist']:
                artist_tags = self.get_artist_tags(artist['name'])
                for tag in artist_tags:
                    genres[tag] += int(artist['playcount'])
            
            # Ordenar y limitar géneros
            top_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)
            period_data['top_genres'] = dict(top_genres[:self.genre_limits[period]])
            
            # Analizar obsesiones
            period_data['obsessions'] = self.analyze_obsessions(period_data, period)
            
            data[period] = period_data
        
        # Obtener historial reciente si es necesario
        if last_timestamp:
            recent_tracks = self.get_recent_tracks(username, last_timestamp)
            data['recent_tracks'] = recent_tracks
        
        # Guardar datos
        self.save_data(username, 'full_data', data)

    def process_year(self, username: str, year: int, force_update: bool = False):
        """Procesa los datos de un año específico"""
        # Comprobar si ya tenemos datos recientes
        existing_data = self.data_manager.load_data(
            'year_data',
            username=username,
            year=year
        )
        
        update_interval = timedelta(days=1)  # Actualizar datos diariamente
        storage_path = self.data_manager.get_storage_path(
            'year_data',
            username=username,
            year=year
        )
        
        if not force_update and existing_data and not self.data_manager.should_update(
            storage_path / 'data.json',
            update_interval
        ):
            print(f"Usando datos existentes para {username} año {year}")
            return existing_data
        
        # Si no hay datos o necesitan actualización, procesar
        data = {
            'username': username,
            'year': year,
            'annual': None,
            'monthly': {},
            'weekly': {}
        }
        

        # Datos anuales
        annual_data = {
            'top_tracks': self.get_user_top_tracks(username, '12month'),
            'top_artists': self.get_user_top_artists(username, '12month'),
            'top_albums': self.get_user_top_albums(username, '12month')
        }
        data['annual'] = annual_data

        # Datos mensuales
        for date in self.get_monthly_dates(year):
            if date <= datetime.now():  # Solo procesar hasta el mes actual
                monthly_data = {
                    'top_tracks': self.get_user_top_tracks(username, 'monthly'),
                    'top_artists': self.get_user_top_artists(username, 'monthly'),
                    'top_albums': self.get_user_top_albums(username, 'monthly')
                }
                data['monthly'][date.strftime('%Y-%m')] = monthly_data

        # Datos semanales
        for date in self.get_weekly_dates(year):
            if date <= datetime.now():  # Solo procesar hasta la semana actual
                weekly_data = {
                    'top_tracks': self.get_user_top_tracks(username, 'weekly'),
                    'top_artists': self.get_user_top_artists(username, 'weekly'),
                    'top_albums': self.get_user_top_albums(username, 'weekly')
                }
                data['weekly'][date.strftime('%Y-%m-%d')] = weekly_data

        # Guardar datos
        self.data_manager.save_data(
            data,
            'year_data',
            username=username,
            year=year
        )
        return data

def main():
    parser = argparse.ArgumentParser(description='Recolector de datos de LastFM')
    parser.add_argument('--api-key', required=True, help='API Key de LastFM')
    parser.add_argument('--users', required=True, nargs='+', help='Lista de usuarios')
    parser.add_argument('--year', type=int, help='Año específico')
    parser.add_argument('--force-update', action='store_true', 
                       help='Forzar actualización de datos existentes')
    
    args = parser.parse_args()
    
    collector = LastFMDataCollector(args.api_key)
    
    if args.year:
        # Procesar año específico
        for username in args.users:
            collector.process_year(
                username,
                args.year,
                force_update=args.force_update
            )
    
    # Buscar coincidencias si hay múltiples usuarios
    if len(args.users) > 1:
        collector.find_unique_coincidences(
            args.users,
            year=args.year
        )

if __name__ == "__main__":
    main()