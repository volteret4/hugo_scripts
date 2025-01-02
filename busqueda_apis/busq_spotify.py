#!/usr/bin/env python3
#
# Script Name: spotify.py
# Description: Obtener link de Spotify para el artista, álbum o canción pasado como argumento.
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
import base64
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Acceder a las variables de entorno.
CLIENT_ID = os.getenv('SPOTIFY_CLIENT')
SECRET_ID = os.getenv('SPOTIFY_SECRET')

def get_access_token(CLIENT_ID, SECRET_ID):
    try:
        # Construye las credenciales codificadas en base64
        credentials = f"{CLIENT_ID}:{SECRET_ID}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        # Construye el cuerpo de la solicitud para obtener el token de acceso
        data = {"grant_type": "client_credentials"}
        headers = {"Authorization": f"Basic {encoded_credentials}"}

        # Realiza la solicitud POST para obtener el token de acceso
        response = requests.post("https://accounts.spotify.com/api/token", data=data, headers=headers)
        response.raise_for_status()  # Lanza una excepción si hay un error en la solicitud
        access_token = response.json()["access_token"]

        return access_token

    except requests.exceptions.RequestException as e:
        print("Error al obtener el token de acceso:", e)
        return None

def search_spotify(query, search_type, access_token):
    try:
        # Construye la URL de búsqueda en la API de Spotify
        search_url = f"https://api.spotify.com/v1/search?q={query}&type={search_type}"

        # Realiza la solicitud GET a la API de Spotify
        response = requests.get(search_url, headers={"Authorization": f"Bearer {access_token}"})
        response.raise_for_status()  # Lanza una excepción si hay un error en la solicitud
        data = response.json()

        # Procesa y devuelve el primer resultado
        if search_type in data and "items" in data[search_type] and len(data[search_type]["items"]) > 0:
            item_url = data[search_type]["items"][0]["external_urls"]["spotify"]
            return item_url
        else:
            print(f"No se encontraron resultados para {search_type}: {query}.")
            return None

    except requests.exceptions.RequestException as e:
        print("Error al hacer la solicitud a la API de Spotify:", e)
        return None

if __name__ == "__main__":
    # Verifica que se pasen los argumentos correctos
    if len(sys.argv) < 2:
        print("Uso: python spotify.py <query>")
        sys.exit(1)

    # Obtiene el token de acceso de Spotify
    access_token = get_access_token(CLIENT_ID, SECRET_ID)

    if access_token:
        # Concatena todos los argumentos como una única consulta
        query = " ".join(sys.argv[1:])
        
        # Busca en Spotify y obtén la URL correspondiente
        item_types = ["artist", "album", "track"]  # Puedes ajustar los tipos según tu necesidad
        for item_type in item_types:
            item_url = search_spotify(query, item_type, access_token)
            if item_url:
                print(f"Enlace de {item_type}: {item_url}")
                break