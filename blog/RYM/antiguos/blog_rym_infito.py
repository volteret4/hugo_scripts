import requests
from collections import Counter
from dotenv import load_dotenv
import os
import markdown
import sys

load_dotenv()

# Tu API key de Last.fm
API_KEY = os.getenv('LASTFM_API_KEY')
BASE_URL = "http://ws.audioscrobbler.com/2.0/"

# Lista de usuarios que quieres analizar
USERNAMES = ["paqueradejere", "sdecandelario", "Nubis84", "BipolarMuzik", "bloodinmyhand", "EliasJ72", "Rocky_stereo", "Frikomid", "alberto_gu", "Music-is-Crap", "GabredMared", "Mister_Dimentio"]  # Aquí defines los usuarios que quieres consultar

class LastFMStats:
    def __init__(self, api_key, usernames):
        self.api_key = api_key
        self.usernames = usernames
        self.base_url = "http://ws.audioscrobbler.com/2.0/"

    def _make_request(self, method, username, params=None):
        default_params = {
            'method': method,
            'api_key': self.api_key,
            'username': username,
            'format': 'json',
            'period': '7day'
        }
        if params:
            default_params.update(params)
        
        try:
            response = requests.get(self.base_url, params=default_params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error consultando datos para {username}: {e}", file=sys.stderr)
            return None

    def get_all_tracks(self, username):
        tracks = {}
        try:
            page = 1
            while True:
                params = {
                    'page': page,
                    'limit': 200  # Máximo permitido por la API
                }
                data = self._make_request('user.getrecenttracks', username, params)
                
                if not data or 'recenttracks' not in data:
                    print(f"Perfil privado o sin datos para {username}", file=sys.stderr)
                    return None
                
                for track in data['recenttracks'].get('track', []):
                    if track.get('nowplaying', False):
                        continue
                    
                    track_name = track['name']
                    artist_name = track['artist']['#text']
                    album_name = track.get('album', {}).get('#text', 'Unknown Album')
                    
                    key = (track_name, artist_name, album_name)
                    tracks[key] = tracks.get(key, 0) + 1
                
                total_pages = int(data['recenttracks']['@attr']['totalPages'])
                if page >= total_pages:
                    break
                page += 1
            
            return tracks
        except Exception as e:
            print(f"Error procesando tracks de {username}: {e}", file=sys.stderr)
            return None

    def generate_markdown(self):
        # Filtrar usuarios con datos disponibles
        valid_users_tracks = {}
        for user in self.usernames:
            user_tracks = self.get_all_tracks(user)
            if user_tracks is not None:
                valid_users_tracks[user] = user_tracks
        
        # Actualizar lista de usuarios
        self.usernames = list(valid_users_tracks.keys())
        
        md_content = "# Last.fm Weekly Statistics\n\n"
        md_content += "## Intersecciones entre Usuarios\n\n"
        
        # Tracks compartidas
        shared_tracks = []
        all_tracks = set()
        for user_tracks in valid_users_tracks.values():
            all_tracks.update(user_tracks.keys())
        
        for track in all_tracks:
            track_users = {}
            for user, user_tracks in valid_users_tracks.items():
                if track in user_tracks:
                    track_users[user] = user_tracks[track]
            
            if len(track_users) > 1:
                shared_tracks.append((track, track_users))
        
        if shared_tracks:
            md_content += "### Canciones Compartidas\n"
            md_content += "| Canción | Artista | Álbum | " + " | ".join(self.usernames) + " |\n"
            md_content += "|---------|---------|-------|" + "|".join(["----------"] * len(self.usernames)) + "|\n"
            
            for (track_name, artist_name, album_name), plays_by_user in shared_tracks:
                plays = [plays_by_user.get(user, 0) for user in self.usernames]
                md_content += f"| {track_name} | {artist_name} | {album_name} | " + " | ".join(map(str, plays)) + " |\n"
        
        return md_content

    def save_markdown(self, filename):
        content = self.generate_markdown()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

# Ejemplo de uso
def main():
    lastfm_stats = LastFMStats(API_KEY, USERNAMES)
    lastfm_stats.save_markdown('lastfm_weekly_stats.md')

if __name__ == "__main__":
    main()
