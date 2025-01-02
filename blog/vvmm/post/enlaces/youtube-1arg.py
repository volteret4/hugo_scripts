#!/usr/bin/env python3
#
# Script Name: youtube-1arg.py
# Description: Obtener link de playlist de youtube para el album pasado como argumento. 
# Author: volteret4
# Repository: https://github.com/volteret4/
# License:
# TODO: 
# Notes:
#   Dependencies:   - python3, requests, dotenv
#                   - .env file
#

from googleapiclient.discovery import build
import sys
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Acceder a las variables de entorno
YT_TOKEN = os.getenv('YT_TOKEN')

def buscar_videos(busqueda, YT_TOKEN):
    youtube = build('youtube', 'v3', developerKey=YT_TOKEN)

    # Realizar la búsqueda de videos relacionados con el busqueda
    search_response = youtube.search().list(
        q=busqueda,
        part='id,snippet',
        maxResults=5
    ).execute()

    # Obtener las URLs de los videos si se encuentran
    videos = []
    for item in search_response['items']:
        if item['id']['kind'] == 'youtube#video':
            video_id = item['id']['videoId']
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            videos.append(video_url)

    return videos

# Ejemplo de uso
if __name__ == "__main__":
    busqueda = sys.argv[1]

    urls_videos = buscar_videos(busqueda, YT_TOKEN)
    if urls_videos:
        for url in urls_videos:
            print(url)
#    else:
#      print("No se encontró ninguna playlist.")
