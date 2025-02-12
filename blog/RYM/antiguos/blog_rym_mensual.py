import requests
from collections import defaultdict
from dotenv import load_dotenv
import os
import markdown
import sys
from datetime import datetime, timedelta
import argparse
import calendar

load_dotenv()

# Tu API key de Last.fm
#filename="/home/pi/hugo/web/rym/lastfm_monthly_stats.md"
API_KEY = os.getenv('LASTFM_API_KEY')
BASE_URL = "http://ws.audioscrobbler.com/2.0/"
fecha_actual = datetime.now()
fecha_formateada = fecha_actual.strftime("%d-%m-%Y")

# Lista de usuarios que quieres analizar
USERNAMES = [
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

class LastFMStats:
    def __init__(self, api_key, usernames, year=None, month=None):
    # Si no se especifica año y mes, usar el mes anterior
        if year is None or month is None:
            now = datetime.now()
            if month is None:
                # Si estamos en enero, ir al diciembre del año anterior
                if now.month == 1:
                    month = 12
                    year = now.year - 1
                else:
                    month = now.month - 1
                    year = now.year
        
        # Obtener el primer y último día del mes especificado
        first_day = datetime(year, month, 1)
        _, last_day_of_month = calendar.monthrange(year, month)
        last_day = datetime(year, month, last_day_of_month, 23, 59, 59)
        
        self.start_timestamp = int(first_day.timestamp())
        self.end_timestamp = int(last_day.timestamp())
        self.month_name = first_day.strftime("%B %Y")
        
        self.api_key = api_key
        self.usernames = usernames
        self.base_url = "http://ws.audioscrobbler.com/2.0/"
    
    def _make_request(self, method, username, params=None):
        default_params = {
            'method': method,
            'api_key': self.api_key,
            'username': username,
            'format': 'json',
        }
        if params:
            default_params.update(params)
        
        try:
            print(f"🔍 Consultando datos para {username}...", file=sys.stderr)
            response = requests.get(self.base_url, params=default_params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error consultando datos para {username}: {e}", file=sys.stderr)
            return None


    def get_tracks_last_week(self, username):
        tracks = defaultdict(int)
        albums = defaultdict(lambda: defaultdict(int))
        artists = defaultdict(int)
        
        try:
            page = 1
            tracks_in_month = 0
            max_tracks_per_user = 100000
            total_tracks_found = 0
            
            while True:
                print(f"🔍 Debugging {username}: Página {page}", file=sys.stderr)
                
                params = {
                    'page': page,
                    'limit': 200,
                    'from': self.start_timestamp,
                    'to': self.end_timestamp
                }
                data = self._make_request('user.getrecenttracks', username, params)
                
                if not data:
                    print(f"❌ NO DATA for {username}", file=sys.stderr)
                    return None, None, None
                
                if 'recenttracks' not in data:
                    print(f"❌ NO RECENTTRACKS for {username}", file=sys.stderr)
                    print(f"API Response: {data}", file=sys.stderr)
                    return None, None, None
                
                tracks_list = data['recenttracks'].get('track', [])
                print(f"📊 Tracks in this page: {len(tracks_list)}", file=sys.stderr)
                
                if not tracks_list:
                    print(f"❌ EMPTY TRACKS LIST for {username}", file=sys.stderr)
                    break
                
                for track in tracks_list:
                    # Skip now playing track if needed
                    if track.get('nowplaying', False):
                        print("⏭️ Skipping now playing track", file=sys.stderr)
                        continue
                    
                    # Ensure track has a date
                    track_date = int(track.get('date', {}).get('uts', 0))
                    
                    track_name = track.get('name', 'Unknown Track')
                    artist_name = track.get('artist', {}).get('#text', 'Unknown Artist')
                    album_name = track.get('album', {}).get('#text', 'Unknown Album')
                    
                    # Add track details
                    tracks[(track_name, artist_name, album_name)] += 1
                    albums[album_name][artist_name] += 1
                    artists[artist_name] += 1
                    
                    total_tracks_found += 1
                    tracks_in_month += 1
                    
                    if tracks_in_month >= max_tracks_per_user:
                        break
                
                print(f"🎵 Total tracks found so far: {total_tracks_found}", file=sys.stderr)
                
                # Check pagination
                total_pages = int(data['recenttracks']['@attr'].get('totalPages', 1))
                print(f"📄 Total pages: {total_pages}, Current page: {page}", file=sys.stderr)
                
                if page >= total_pages or tracks_in_month >= max_tracks_per_user:
                    break
                
                page += 1
            
            print(f"✅ Final track count for {username}: {total_tracks_found}", file=sys.stderr)
            return tracks, albums, artists
        
        except Exception as e:
            print(f"❌ EXCEPTION for {username}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return None, None, None
    def get_top_10(self, data):
        return dict(sorted(data.items(), key=lambda x: x[1], reverse=True)[:10])

    def generate_markdown(self):
        valid_users_data = {}
        for user in self.usernames:
            user_tracks, user_albums, user_artists = self.get_tracks_last_week(user)
            if user_tracks is not None:
                valid_users_data[user] = {
                    'tracks': user_tracks,
                    'albums': user_albums,
                    'artists': user_artists
                }
        
        self.usernames = list(valid_users_data.keys())
        
        md_content = f"# Estadísticas de Last.fm - {self.month_name}\n\n"
        
        # Coincidencias
        md_content += "## Coincidencias entre Usuarios\n\n"
        
        # Canciones compartidas
        md_content += "### Canciones\n"
        md_content += "| Canción | Artista | Álbum | Usuarios |\n"
        md_content += "|---------|---------|-------|----------|\n"
        shared_tracks = {}
        all_tracks = set()
        for user_data in valid_users_data.values():
            all_tracks.update(user_data['tracks'].keys())
        
        for track in all_tracks:
            track_users = {}
            for user, user_data in valid_users_data.items():
                if track in user_data['tracks']:
                    track_users[user] = user_data['tracks'][track]
            
            if len(track_users) > 1:
                track_name, artist_name, album_name = track
                shared_tracks[track] = {
                'track_name': track_name,
                'artist_name': artist_name,
                'album_name': album_name,
                'users': track_users
            }
                # Ordenar tracks por número de usuarios (de mayor a menor)
        sorted_tracks = sorted(
            shared_tracks.values(), 
            key=lambda x: len(x['users']), 
            reverse=True
        )
        for track_info in sorted_tracks:
            user_plays = [f"{user} ({plays})" for user, plays in track_info['users'].items()]
            md_content += f"| {track_info['track_name']} | {track_info['artist_name']} | {track_info['album_name']} | {', '.join(user_plays)} |\n"
        
                # user_plays = [f"{user} ({plays})" for user, plays in track_users.items()]
                # md_content += f"| {track_name} | {artist_name} | {album_name} | {', '.join(user_plays)} |\n"
        
        # Álbumes compartidos
        md_content += "\n### Álbumes\n"
        md_content += "| Álbum | Artista | Usuarios |\n"
        md_content += "|-------|---------|----------|\n"
        shared_albums = {}

        all_albums = set()
        for user_data in valid_users_data.values():
            all_albums.update(user_data['albums'].keys())
        
        for album in all_albums:
            album_users = {}
            for user, user_data in valid_users_data.items():
                if album in user_data['albums']:
                    album_users[user] = sum(user_data['albums'][album].values())
            
            if len(album_users) > 1:
                artist = next(iter(set(artist for user_data in valid_users_data.values() for artist in user_data['albums'][album].keys())))
                shared_albums[album] = {
                'album': album,
                'artist': artist,
                'users': album_users
            }

            # Ordenar álbumes por número de usuarios (de mayor a menor)
        sorted_albums = sorted(
            shared_albums.values(), 
            key=lambda x: len(x['users']), 
            reverse=True
        )
        
        for album_info in sorted_albums:
            user_plays = [f"{user} ({plays})" for user, plays in album_info['users'].items()]
            md_content += f"| {album_info['album']} | {album_info['artist']} | {', '.join(user_plays)} |\n"
                # user_plays = [f"{user} ({plays})" for user, plays in album_users.items()]
                # md_content += f"| {album} | {artist} | {', '.join(user_plays)} |\n"
        
        # Artistas compartidos
        md_content += "\n### Artistas\n"
        md_content += "| Artista | Usuarios |\n"
        md_content += "|---------|----------|\n"
        shared_artists = {}

        all_artists = set()
        for user_data in valid_users_data.values():
            all_artists.update(user_data['artists'].keys())
        
        for artist in all_artists:
            artist_users = {}
            for user, user_data in valid_users_data.items():
                if artist in user_data['artists']:
                    artist_users[user] = user_data['artists'][artist]
            
            if len(artist_users) > 1:
                shared_artists[artist] = artist_users
        # Ordenar artistas por número de usuarios (de mayor a menor)
        sorted_artists = sorted(
            shared_artists.items(), 
            key=lambda x: len(x[1]), 
            reverse=True
        )
        
        for artist, artist_users in sorted_artists:
            user_plays = [f"{user} ({plays})" for user, plays in artist_users.items()]
            md_content += f"| {artist} | {', '.join(user_plays)} |\n"
    
                # user_plays = [f"{user} ({plays})" for user, plays in artist_users.items()]
                # md_content += f"| {artist} | {', '.join(user_plays)} |\n"
        
        # Top 10 por usuario
        for user, data in valid_users_data.items():
            md_content += f"## Top 10 para {user}\n\n"
            
            md_content += "*Top Artistas*\n"
            md_content += "| Artista | Reproducciones |\n|---------|----------------|\n"
            for artist, plays in self.get_top_10(data['artists']).items():
                md_content += f"| {artist} | {plays} |\n"
            md_content += "\n"

            md_content += "*Top Canciones*\n"
            md_content += "| Canción | Artista | Álbum | Reproducciones |\n|---------|----------|-------|----------------|\n"
            for (track, artist, album), plays in self.get_top_10(data['tracks']).items():
                md_content += f"| {track} | {artist} | {album} | {plays} |\n"
            md_content += "\n"

      
        return md_content

    def save_markdown(self, filename):
        content = self.generate_markdown()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

# Ejemplo de uso
def main():

    # Buscar los valores de --year y --month en los argumentos
    args = sys.argv
    year = None
    month = None

    # Recorrer los argumentos y extraer los valores
    for i in range(len(args)):
        if args[i] == "--year" and i + 1 < len(args):
            year = args[i + 1]
        elif args[i] == "--month" and i + 1 < len(args):
            month = args[i + 1]

    # Verificar que ambos valores fueron encontrados
    if year and month:
        fecha_formateada = f"{month}-{year}"
        print(f"Fecha formateada: {fecha_formateada}")
        # Convertir year y month a enteros antes de pasarlos
        year_int = int(year)
        month_int = int(month)
        lastfm_stats = LastFMStats(API_KEY, USERNAMES, year=year_int, month=month_int)
        lastfm_stats.save_markdown(fecha_formateada)

if __name__ == "__main__":
    main()
