
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

load_dotenv()
DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN")

# Configurar MusicBrainz
musicbrainzngs.set_useragent("PortadaDownloader", "1.0", "your-email@example.com")  # Cambia por tu email válido

def buscar_portada(artista, album):
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
        else:
            print(f"Error al descargar portada: {response.status_code}")
    except Exception as e:
        print(f"Error descargando portada: {e}")

def main():
    parser = argparse.ArgumentParser(description="Descarga la portada de un álbum desde MusicBrainz.")
    parser.add_argument("artista", help="Nombre del artista.")
    parser.add_argument("album", help="Nombre del álbum.")
    parser.add_argument("ruta", help="Ruta completa donde guardar la portada (sin incluir el nombre del archivo).")
    args = parser.parse_args()

    portada_url = buscar_portada(args.artista, args.album)
    if portada_url:
        print(f"Portada encontrada: {portada_url}")
        descargar_portada(args.artista, args.album, portada_url, args.ruta)
    else:
        print("No se encontró la portada en MusicBrainz.")

if __name__ == "__main__":
    main()
