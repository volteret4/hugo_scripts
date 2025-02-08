#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

class LastFMWeeklyListenings:
    def __init__(self, username, api_key):
        """
        Inicializa el extractor de escuchas semanales de Last.fm
        
        :param username: Nombre de usuario de Last.fm
        :param api_key: Clave de API de Last.fm
        """
        self.username = username
        self.api_key = api_key
        self.base_url = "http://ws.audioscrobbler.com/2.0/"
    
    def get_weekly_albums(self, limit=10):
        """
        Obtiene los álbumes más escuchados en la semana actual
        
        :param limit: Número máximo de álbumes a devolver
        :return: Lista de álbumes con su información
        """
        # Parámetros para la solicitud de API
        params = {
            'method': 'user.gettopalbums',
            'user': self.username,
            'api_key': self.api_key,
            'period': '7day',  # Últimos 7 días
            'format': 'json',
            'limit': limit
        }
        
        try:
            # Realizar solicitud a Last.fm
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            # Procesar respuesta
            data = response.json()
            top_albums = data.get('topalbums', {}).get('album', [])
            
            # Formatear álbumes
            formatted_albums = []
            for album in top_albums:
                formatted_albums.append({
                    'artist': album.get('artist', {}).get('name', 'Desconocido'),
                    'album': album.get('name', 'Desconocido'),
                    'plays': int(album.get('playcount', 0))
                })
            
            return formatted_albums
        
        except requests.RequestException as e:
            print(f"Error obteniendo datos de Last.fm: {e}")
            return []
    
    def save_weekly_listening_json(self, filename='weekly_listening.json'):
        """
        Guarda los álbumes más escuchados en un archivo JSON
        
        :param filename: Nombre del archivo JSON a guardar
        """
        # Obtener álbumes de la semana
        weekly_albums = self.get_weekly_albums()
        
        # Guardar en archivo JSON
        with open(filename, 'w') as f:
            json.dump(weekly_albums, f, indent=2)
        
        print(f"Datos de escuchas guardados en {filename}")

def main():
    # Configurar con tus credenciales de Last.fm



    # Tu API key de Last.fm
    API_KEY = os.getenv('LASTFM_API_KEY')
    USERNAME = os.getenv('LASTFM_USERNAME')

    # Crear instancia y guardar datos
    lastfm_listener = LastFMWeeklyListenings(USERNAME, API_KEY)
    lastfm_listener.save_weekly_listening_json()

if __name__ == '__main__':
    main()