import spotipy
from spotipy.oauth2 import SpotifyOAuth
import sys
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Acceder a las variables de entorno.
CLIENT_ID = os.getenv('SPOTIFY_CLIENT')
CLIENT_SECRET = os.getenv('SPOTIFY_SECRET')
redirect_uri = 'http://127.0.0.1:8090'
scope = "playlist-read-private"
browser = False
cache_path = "/home/ansible/scripts/playlists/spotify/token.txt"

artista = sys.argv[1]
titulo = sys.argv[2]

sp_oauth = SpotifyOAuth(CLIENT_ID, CLIENT_SECRET, redirect_uri, scope, browser, cache_path)

# Obtiene el token de acceso de la caché o solicita uno nuevo si no está en la caché o ha caducado
token_info = sp_oauth.get_cached_token()

# Si obtienes un token de acceso, inicializa el cliente de Spotify
if token_info:
    access_token = token_info['access_token']
    sp = spotipy.Spotify(auth=access_token)

    # Función para buscar una canción por artista y título
    def buscar_cancion(artista, titulo):
        # Formatea la consulta de búsqueda
        query = f'artist:{artista} track:{titulo}'

        # Realiza la búsqueda en la API de Spotify
        resultados = sp.search(q=query, type='track', limit=1)

        # Comprueba si se encontraron resultados
        if resultados['tracks']['items']:
            # Obtiene la primera canción encontrada
            cancion = resultados['tracks']['items'][0]
            # Imprime la ID y la URL de la canción encontrada
            print(cancion['id'])
            print(cancion['external_urls']['spotify'])
        else:
            print("nocancion.")

    # Llama a la función para buscar la canción
    buscar_cancion(artista, titulo)
else:
    print("notoken")
