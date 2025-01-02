
#!/usr/bin/env python
#
# Script Name: yt_get_playlist.py
# Description:
# Author: volteret4
# Repository: https://github.com/volteret4/
# License:
# TODO:
# Notes:
#   Dependencies:  - python3,
#

import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

# Configuración
scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
client_secrets_file = "client_secret.json"  # Este archivo lo obtuviste de Google Cloud Console

# Obtener credenciales y crear una API client
def get_authenticated_service():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    
    auth_url, _ = flow.authorization_url(prompt='consent')
    print(f"Por favor, abre esta URL en un navegador: {auth_url}")
    
    # Pide el código de autorización al usuario
    code = input("Introduce el código de autorización: ")
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

# Obtener listas de reproducción
def get_playlists(service):
    request = service.playlists().list(
        part="snippet,contentDetails",
        mine=True,
        maxResults=50
    )
    response = request.execute()
    
    for playlist in response.get("items", []):
        print(f"Title: {playlist['snippet']['title']}")
        print(f"ID: {playlist['id']}")
        print()

if __name__ == "__main__":
    youtube_service = get_authenticated_service()
    get_playlists(youtube_service)