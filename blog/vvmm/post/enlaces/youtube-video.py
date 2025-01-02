import sys
import os
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Acceder a las variables de entorno
YT_TOKEN = os.getenv('YT_TOKEN')

if not YT_TOKEN:
    print("Error: Debes configurar la variable de entorno YOUTUBE_YT_TOKEN con tu clave de API de YouTube.")
    sys.exit(1)

# Crear el cliente de la API de YouTube
youtube = build('youtube', 'v3', developerKey=YT_TOKEN)

def search_first_video_url(query):
    # Realizar la búsqueda
    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        maxResults=1  # Solo necesitamos el primer resultado
    ).execute()

    # Procesar el resultado
    if search_response['items']:
        item = search_response['items'][0]
        if item['id']['kind'] == 'youtube#video':
            return f"https://www.youtube.com/watch?v={item['id']['videoId']}"
    
    return "Nada"

if len(sys.argv) < 2:
    print("Uso: python search_youtube.py <término de búsqueda>")
    sys.exit()

search_term = ' '.join(sys.argv[1:])
video_url = search_first_video_url(search_term)

print(video_url)
