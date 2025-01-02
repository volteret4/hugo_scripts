#!/usr/bin/env python3
#
# Script Name: genius.py
# Description: Obtener link de genius para el album pasado como argumento.
# Author: volteret4
# Repository: https://github.com/volteret4/
# License:
# TODO: 
# Notes:
#   Dependencies:   - python3, requests, dotenv
#                   - .env file
#

import requests
import sys
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Acceder a las variables de entorno
GENIUS_CLIENT = os.getenv('GENIUS_CLIENT')
GENIUS_SECRET = os.getenv('GENIUS_SECRET')

def search_album(artist_name, album_title):
    # Inserta tu GENIUS_CLIENT y GENIUS_SECRET

    
    # Realiza la autenticación para obtener el token de acceso
    auth_url = 'https://api.genius.com/oauth/token'
    auth_data = {
        'GENIUS_CLIENT': GENIUS_CLIENT,
        'GENIUS_SECRET': GENIUS_SECRET,
        'grant_type': 'client_credentials'
    }
    auth_response = requests.post(auth_url, data=auth_data)
    access_token = auth_response.json()['access_token']
    
    # Construye la URL de búsqueda
    search_url = f'https://api.genius.com/search?q={artist_name} {album_title}'
    
    # Agrega el token de acceso a los encabezados de la solicitud
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Realiza la solicitud de búsqueda
    response = requests.get(search_url, headers=headers)
    data = response.json()
    
    # Verifica si se encontraron resultados
    if 'response' in data and 'hits' in data['response'] and len(data['response']['hits']) > 0:
        # Obtén la URL del primer resultado (asumiendo que es el álbum buscado)
        album_url = data['response']['hits'][0]['result']['url']
        return album_url
    else:
        return None

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python genius_album.py [artista] [album]")
        sys.exit(1)
    
    artist_name = sys.argv[1]
    album_title = sys.argv[2]
    
    album_url = search_album(artist_name, album_title)
    if album_url:
        print(f"URL del álbum '{album_title}' de '{artist_name}': {album_url}")
    else:
        print(f"No se encontró el álbum '{album_title}' de '{artist_name}'.")