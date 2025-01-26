
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
#   Requiere 2 argumentos, artista y album.

import requests
import argparse
from pathlib import Path
import musicbrainzngs
import os
from dotenv import load_dotenv
import discogs_client
import json

load_dotenv()
DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN")
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

# Configurar MusicBrainz y Discogs
musicbrainzngs.set_useragent("PortadaDownloader", "1.0", "your-email@example.com")
discogs = discogs_client.Client('PortadaDownloader/1.0', user_token=DISCOGS_TOKEN)

def buscar_portada_musicbrainz(artista, album):
    """Busca la URL de la portada en MusicBrainz."""
    try:
        resultados = musicbrainzngs.search_releases(artist=artista, release=album, limit=1)
        if resultados['release-list']:
            release = resultados['release-list'][0]
            release_id = release['id']
            return f"https://coverartarchive.org/release/{release_id}/front"
        return None
    except Exception as e:
        print(f"Error buscando en MusicBrainz: {e}")
        return None

def buscar_portada_discogs(artista, album):
    """Busca la URL de la portada en Discogs."""
    try:
        results = discogs.search(f"{artista} - {album}", type='release')
        if results:
            release = results[0]
            if hasattr(release, 'images') and release.images:
                return release.images[0]['uri']
        return None
    except Exception as e:
        print(f"Error buscando en Discogs: {e}")
        return None

def buscar_portada_lastfm(artista, album):
    """Busca la URL de la portada en Last.fm."""
    try:
        url = f"http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key={LASTFM_API_KEY}&artist={artista}&album={album}&format=json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'album' in data and 'image' in data['album']:
                # Obtener la imagen más grande disponible
                images = data['album']['image']
                for img in reversed(images):  # Reversed para obtener primero la más grande
                    if img['#text']:
                        return img['#text']
        return None
    except Exception as e:
        print(f"Error buscando en Last.fm: {e}")
        return None

def descargar_portada(artista, album, url, ruta_archivo):
    """Descarga y guarda la portada en la ruta especificada."""
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            nombre_archivo = f"{artista}-_-{album}".replace(' ', '-')
            nombre_archivo = "".join(c for c in nombre_archivo if c.isalnum() or c in ('_', '-')).rstrip()
            ruta_archivo = os.path.join(ruta_archivo, f"image.jpeg")
            with open(ruta_archivo, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Portada guardada en: {ruta_archivo}")
            return True
        else:
            print(f"Error al descargar portada: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error descargando portada: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Descarga la portada de un álbum desde varias fuentes.")
    parser.add_argument("artista", help="Nombre del artista.")
    parser.add_argument("album", help="Nombre del álbum.")
    parser.add_argument("ruta", help="Ruta completa donde guardar la portada (sin incluir el nombre del archivo).")
    args = parser.parse_args()

    # Intentar cada fuente en orden hasta que una funcione
    fuentes = [
        ('MusicBrainz', buscar_portada_musicbrainz),
        ('Discogs', buscar_portada_discogs),
        ('Last.fm', buscar_portada_lastfm)
    ]

    for nombre_fuente, buscar_funcion in fuentes:
        print(f"Buscando en {nombre_fuente}...")
        portada_url = buscar_funcion(args.artista, args.album)
        
        if portada_url:
            print(f"Portada encontrada en {nombre_fuente}: {portada_url}")
            if descargar_portada(args.artista, args.album, portada_url, args.ruta):
                break
    else:
        print("No se pudo encontrar o descargar la portada de ninguna fuente.")

if __name__ == "__main__":
    main()