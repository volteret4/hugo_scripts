#!/usr/bin/env python3
#
# Script Name: releases_discogs.py
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


# Establecer variables.     # Acceder a las variables de entorno    # se puede pasar album como * para obtener todos los releases
BASE_URL = "https://api.discogs.com"
TOKEN = os.getenv('DISCOGS_TOKEN')

def get_artist_releases(artist_id):
    # Construye la URL para obtener los releases del artista
    releases_url = f"{BASE_URL}/artists/{artist_id}/releases?token={TOKEN}"

    try:
        # Realiza la solicitud GET para obtener los releases del artista
        response = requests.get(releases_url)
        response.raise_for_status()  # Lanza una excepción si hay un error en la solicitud

        # Analiza la respuesta JSON
        data = response.json()

        # Retorna los releases del artista
        return data['releases']

    except requests.exceptions.RequestException as e:
        print("Error al hacer la solicitud a la API de Discogs:", e)
        return None

def get_master_release_id(artist_name, album_name):
    # Construye la URL para buscar el álbum por artista y nombre de álbum
    search_url = f"{BASE_URL}/database/search?q={artist_name} {album_name}&type=master&token={TOKEN}"

    try:
        # Realiza la solicitud GET a la API de Discogs
        response = requests.get(search_url)
        response.raise_for_status()  # Lanza una excepción si hay un error en la solicitud

        # Analiza la respuesta JSON
        data = response.json()

        # Verifica si hay resultados
        if data['pagination']['items'] == 0:
            print(f"No se encontraron resultados para el álbum '{album_name}' del artista '{artist_name}'.")
            print("Álbumes encontrados:")
            for result in data['results']:
                print(f"- {result['title']}")
            return None

        # Obtiene el ID del master release del primer resultado
        artist_id = data['results'][0]['id']
        artist_releases = get_artist_releases(artist_id)
        if artist_releases:
            print("Listado de releases del artista:")
            for release in artist_releases:
                print(f"{release['title']} - {release['year']} - {release['resource_url']}")
        else:
            print("No se pudo obtener el listado de releases del artista.")

        return None

    except requests.exceptions.RequestException as e:
        print("Error al hacer la solicitud a la API de Discogs:", e)
        return None

if __name__ == "__main__":
    # Verifica que se pasen los argumentos correctos
    if len(sys.argv) != 3:
        print("Uso: python discogs_api.py <artista> <álbum>")
        sys.exit(1)

    # Obtén los argumentos del artista y el álbum de la línea de comandos
    artist_name = sys.argv[1]
    album_name = sys.argv[2]

    # Obtiene el ID del master release del álbum especificado
    master_release_id = get_master_release_id(artist_name, album_name)

    if master_release_id:
        print(f"https://www.discogs.com/master/{master_release_id}")
