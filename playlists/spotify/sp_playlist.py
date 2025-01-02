#!/usr/bin/env python
#
# Script Name: sp_playlist.py
# Description: actualizar archivo con nombre e id de playlists de spotify
# Author: volteret4
# Repository: https://github.com/volteret4/
# License:
# TODO: 
# Notes:
#   Dependencies:  - python3, 
#
#   No necesita argumentos
#


import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()
home_dir = os.environ["HOME"]

# Acceder a las variables de entorno.
CLIENT_ID = os.getenv('SPOTIFY_CLIENT')
CLIENT_SECRET = os.getenv('SPOTIFY_SECRET')
redirect_uri = 'http://127.0.0.1:8090'

# Cambia el scope para incluir tanto playlists públicas como privadas
scope = "playlist-read-private playlist-read-collaborative"

cache_path = os.path.join(home_dir, "hugo", "scripts", "playlists", "spotify", "token.txt")
playlist = os.path.join(home_dir, "hugo", "scripts", "playlists", "spotify", "playlists.txt")

# Inicializa el cliente de autenticación
sp_oauth = SpotifyOAuth(CLIENT_ID, CLIENT_SECRET, redirect_uri, scope=scope, open_browser=False, cache_path=cache_path)

# Verifica si ya existe un token válido en la caché
token_info = sp_oauth.get_cached_token()

# Si no hay token en la caché, genera la URL para la autenticación manual
if not token_info:
    auth_url = sp_oauth.get_authorize_url()
    print(f"Visita la siguiente URL para autorizar la aplicación:\n{auth_url}")
    # Después de autorizar, obtendrás un "code" en la URL de redirección. Ingrésalo aquí.
    code = input("Ingresa el código que recibiste después de autorizar: ")
    token_info = sp_oauth.get_access_token(code)

# Si tienes un token válido, inicializa el cliente de Spotify
if token_info:
    access_token = token_info['access_token']
    sp = spotipy.Spotify(auth=access_token)

    # Obtiene todas las playlists del usuario (públicas y privadas)
    playlists = sp.current_user_playlists()

    # Abrir el archivo en modo escritura
    with open(playlist, "w") as file:
        # Guarda los nombres y los IDs de las playlists en el archivo
        for playlist in playlists['items']:
            file.write("Nombre: " + playlist['name'] + "\n")
            file.write("ID: " + playlist['id'] + "\n")
            file.write("\n")


    # Guarda el nuevo token en la caché
    sp_oauth._save_token_info(token_info)