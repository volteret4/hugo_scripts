
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

    def get_filename(self, data_type: str, **kwargs) -> str:
        """
        Genera un nombre de archivo descriptivo basado en el tipo y contenido
        """
        if data_type == 'user_data':
            return f"{kwargs['username']}_full_history.json"
        elif data_type == 'year_data':
            return f"{kwargs['username']}_{kwargs['year']}_complete.json"
        elif data_type == 'month_data':
            return f"{kwargs['username']}_{kwargs['year']}_{kwargs['month']:02d}.json"
        elif data_type == 'week_data':
            week_start = kwargs['week_start'].strftime('%Y%m%d')
            return f"{kwargs['username']}_week_{week_start}.json"
        elif data_type == 'coincidences':
            users = sorted(kwargs['users'])
            period = kwargs.get('year', 'all_time')
            return f"coincidences_{'+'.join(users)}_{period}.json"
        elif data_type == 'genres':
            period = kwargs.get('year', 'all_time')
            return f"genres_{kwargs['username']}_{period}.json"
        else:
            raise ValueError(f"Tipo de datos no soportado: {data_type}")


    def get_storage_path(self, data_type: str, **kwargs) -> Path:
        """
        Genera una ruta de almacenamiento organizada basada en el tipo de datos
        """
        base_path = self.base_dir
        
        if data_type == 'user_data':
            base_path = base_path / 'users' / kwargs['username']
        elif data_type == 'year_data':
            base_path = base_path / 'years' / str(kwargs['year'])
        elif data_type == 'month_data':
            base_path = base_path / 'years' / str(kwargs['year']) / 'months'
        elif data_type == 'week_data':
            base_path = base_path / 'years' / str(kwargs['year']) / 'weeks'
        elif data_type == 'coincidences':
            base_path = base_path / 'coincidences'
            if 'year' in kwargs:
                base_path = base_path / str(kwargs['year'])
        elif data_type == 'genres':
            base_path = base_path / 'genres'
            if 'year' in kwargs:
                base_path = base_path / str(kwargs['year'])

        base_path.mkdir(parents=True, exist_ok=True)
        return base_path / self.get_filename(data_type, **kwargs)
    # def should_update_data(self, data_type: str, **kwargs) -> bool:
    #     """Determina si los datos necesitan actualizarse"""
    #     storage_path = self.data_manager.get_storage_path(data_type, **kwargs)
        
    #     if not storage_path.exists():
    #         return True
            
    #     with open(storage_path, 'r', encoding='utf-8') as f:
    #         try:
    #             data = json.load(f)
    #             metadata = data.get('_metadata', {})
    #             created_at = datetime.fromisoformat(metadata.get('created_at', '2000-01-01'))
                
    #             # Si los datos son de hoy, no actualizar
    #             return datetime.now().date() != created_at.date()
    #         except (json.JSONDecodeError, ValueError):
    #             return True

    def save_data(self, data: Dict, data_type: str, **kwargs):
        """Guarda los datos con nombre descriptivo"""
        filepath = self.get_storage_path(data_type, **kwargs)
        
        # Añadir metadatos
        data['_metadata'] = {
            'type': data_type,
            'created_at': datetime.now().isoformat(),
            'parameters': kwargs,
            'version': '1.0'  # Útil para futuras actualizaciones del formato
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"Datos guardados en: {filepath}")

    def list_available_data(self, data_type: str = None, **kwargs) -> List[Path]:
        """Lista los archivos disponibles con filtros opcionales"""
        search_path = self.base_dir
        
        if data_type:
            search_path = search_path / data_type
            if 'year' in kwargs:
                search_path = search_path / str(kwargs['year'])
        
        files = []
        for path in search_path.rglob('*.json'):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)['_metadata']
                    if all(metadata['parameters'].get(k) == v for k, v in kwargs.items()):
                        files.append(path)
            except (json.JSONDecodeError, KeyError):
                continue
                
        return files

    def load_data(self, data_type: str, **kwargs) -> Optional[Dict]:
        """Carga datos si existen"""
        storage_path = self.get_storage_path(data_type, **kwargs)
        
        if storage_path.exists():
            try:
                with open(storage_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error al cargar datos desde {storage_path}")
                return None
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
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    # [Previous methods remain the same...]

    
    def should_update_data(self, data_type: str, **kwargs) -> bool:
        """Determina si los datos necesitan actualizarse"""
        storage_path = self.data_manager.get_storage_path(data_type, **kwargs)
        
        if not storage_path.exists():
            return True
            
        with open(storage_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                metadata = data.get('_metadata', {})
                created_at = datetime.fromisoformat(metadata.get('created_at', '2000-01-01'))
                
                # Si los datos son de hoy, no actualizar
                return datetime.now().date() != created_at.date()
            except (json.JSONDecodeError, ValueError):
                return True

    def _make_request(self, method: str, params: Dict) -> Dict:
        """Método helper para hacer peticiones a la API con reintentos"""
        base_params = {
            'method': method,
            'api_key': self.api_key,
            'format': 'json'
        }
        params.update(base_params)
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(self.base_url, params=params)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 500:
                    print(f"Error 500 en intento {attempt + 1}, reintentando en {self.retry_delay} segundos...")
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"Error en la API: {response.status_code}")
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"Error al procesar petición después de {self.max_retries} intentos: {e}")
                    return {'error': str(e)}
                time.sleep(self.retry_delay)
        return {'error': 'Max retries exceeded'}



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

    def get_weekly_dates(self, year: int) -> List[datetime]:
        """Genera todas las fechas de inicio de semana para un año"""
        start_date = datetime(year, 1, 1)
        dates = []
        
        # Ajustar a lunes
        while start_date.weekday() != 0:  # 0 = Lunes
            start_date += timedelta(days=1)
            
        while start_date.year == year:
            dates.append(start_date)
            start_date += timedelta(weeks=1)
            
        return dates

    def get_monthly_dates(self, year: int) -> List[datetime]:
        """Genera todas las fechas de inicio de mes para un año"""
        return [datetime(year, month, 1) for month in range(1, 13)]

 
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

    def _calculate_coincidences(self, users_data: Dict) -> Dict:
        """Calcula coincidencias entre usuarios"""
        coincidences = {
            'tracks': {},
            'artists': {},
            'albums': {}
        }
        
        # Obtener datos anuales para cada usuario
        user_items = {}
        for username, data in users_data.items():
            user_items[username] = {
                'tracks': set(),
                'artists': set(),
                'albums': set()
            }
            
            annual_data = data.get('annual', {})
            
            # Procesar tracks
            tracks = annual_data.get('top_tracks', {}).get('toptracks', {}).get('track', [])
            for track in tracks:
                track_id = f"{track.get('artist', {}).get('name', '')} - {track.get('name', '')}"
                user_items[username]['tracks'].add(track_id)
            
            # Procesar artists
            artists = annual_data.get('top_artists', {}).get('topartists', {}).get('artist', [])
            for artist in artists:
                user_items[username]['artists'].add(artist.get('name', ''))
            
            # Procesar albums
            albums = annual_data.get('top_albums', {}).get('topalbums', {}).get('album', [])
            for album in albums:
                album_id = f"{album.get('artist', {}).get('name', '')} - {album.get('name', '')}"
                user_items[username]['albums'].add(album_id)

        # Calcular coincidencias para cada tipo
        for item_type in ['tracks', 'artists', 'albums']:
            # Para cada par de usuarios
            for user1, user2 in combinations(users_data.keys(), 2):
                items1 = user_items[user1][item_type]
                items2 = user_items[user2][item_type]
                
                # Encontrar coincidencias
                common_items = items1.intersection(items2)
                
                if common_items:
                    pair_key = f"{user1}-{user2}"
                    coincidences[item_type][pair_key] = list(common_items)

        # Agregar metadatos
        coincidences['metadata'] = {
            'users': list(users_data.keys()),
            'timestamp': datetime.now().isoformat(),
            'total_coincidences': {
                'tracks': sum(len(items) for items in coincidences['tracks'].values()),
                'artists': sum(len(items) for items in coincidences['artists'].values()),
                'albums': sum(len(items) for items in coincidences['albums'].values())
            }
        }

        return coincidences

    def find_unique_coincidences(self, users: List[str], year: Optional[int] = None):
        """Encuentra coincidencias únicas entre usuarios con mejor manejo de caché"""
        if not self.should_update_data('coincidences', users=users, year=year):
            print("Usando coincidencias existentes")
            data = self.data_manager.load_data('coincidences', users=users, year=year)
            if data:
                return data
            print("Datos existentes no válidos, recalculando...")

        print("Calculando nuevas coincidencias")
        users_data = {}
        for username in users:
            print(f"Procesando datos de {username}...")
            if year:
                data = self.process_year(username, year)
            else:
                data = self.process_user(username)
                
            if not data:
                raise Exception(f"No se pudieron obtener datos para el usuario {username}")
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
        """Procesa los datos de un año específico con mejor manejo de caché"""
        if not force_update and not self.should_update_data('year_data', username=username, year=year):
            print(f"Usando datos existentes para {username} año {year}")
            data = self.data_manager.load_data('year_data', username=username, year=year)
            if data:
                return data
            print(f"Datos existentes no válidos para {username}, recopilando nuevos datos...")

        print(f"Recopilando datos nuevos para {username} año {year}")
        data = {
            'username': username,
            'year': year,
            'annual': {},
            'monthly': {},
            'weekly': {}
        }

        try:
            # Datos anuales
            annual_data = {
                'top_tracks': self.get_user_top_tracks(username, '12month'),
                'top_artists': self.get_user_top_artists(username, '12month'),
                'top_albums': self.get_user_top_albums(username, '12month')
            }
            
            # Verificar si alguna llamada a la API falló
            if any('error' in x for x in annual_data.values()):
                raise Exception(f"Error al obtener datos anuales para {username}")
                
            data['annual'] = annual_data

            # Datos mensuales
            for date in self.get_monthly_dates(year):
                if date <= datetime.now():
                    monthly_data = {
                        'top_tracks': self.get_user_top_tracks(username, 'monthly'),
                        'top_artists': self.get_user_top_artists(username, 'monthly'),
                        'top_albums': self.get_user_top_albums(username, 'monthly')
                    }
                    if any('error' in x for x in monthly_data.values()):
                        print(f"Advertencia: Algunos datos mensuales para {username} no pudieron ser obtenidos")
                        continue
                    data['monthly'][date.strftime('%Y-%m')] = monthly_data

            # Datos semanales
            for date in self.get_weekly_dates(year):
                if date <= datetime.now():
                    weekly_data = {
                        'top_tracks': self.get_user_top_tracks(username, 'weekly'),
                        'top_artists': self.get_user_top_artists(username, 'weekly'),
                        'top_albums': self.get_user_top_albums(username, 'weekly')
                    }
                    if any('error' in x for x in weekly_data.values()):
                        print(f"Advertencia: Algunos datos semanales para {username} no pudieron ser obtenidos")
                        continue
                    data['weekly'][date.strftime('%Y-%m-%d')] = weekly_data

            # Guardar datos
            self.data_manager.save_data(
                data,
                'year_data',
                username=username,
                year=year
            )
            return data

        except Exception as e:
            print(f"Error al procesar datos para {username}: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description='Recolector de datos de LastFM')
    parser.add_argument('--api-key', required=True, help='API Key de LastFM')
    parser.add_argument('--users', required=True, nargs='+', help='Lista de usuarios')
    parser.add_argument('--year', type=int, help='Año específico')
    parser.add_argument('--force-update', action='store_true', 
                       help='Forzar actualización de datos existentes')
    
    args = parser.parse_args()
    
    collector = LastFMDataCollector(args.api_key)
    
    try:
        if args.year:
            for username in args.users:
                print(f"Procesando {username} para el año {args.year}...")
                collector.process_year(
                    username,
                    args.year,
                    force_update=args.force_update
                )
        
        if len(args.users) > 1:
            print("Buscando coincidencias entre usuarios...")
            collector.find_unique_coincidences(
                args.users,
                year=args.year
            )
    except Exception as e:
        print(f"Error durante la ejecución: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()