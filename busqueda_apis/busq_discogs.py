import requests
import argparse
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Acceder a las variables de entorno
TOKEN = os.getenv('DISCOGS_TOKEN')
# Configuración de la API de Discogs
BASE_URL = 'https://api.discogs.com/'
HEADERS = {'User-Agent': 'YourApp/1.0', 'Authorization': 'Discogs token=YOUR_DISCOGS_API_KEY'}

def search_discogs(query):
    # Función para buscar en Discogs según la consulta combinada
    try:
        # Comenzamos buscando como master release
        master_search_url = f'{BASE_URL}database/search?q={query}&type=master&token={TOKEN}'
        response = requests.get(master_search_url, headers=HEADERS)
        master_results = response.json()

        if 'results' in master_results and master_results['results']:
            master_id = master_results['results'][0]['master_id']
            print(f'Encontrado como master release: {master_id}')
            return

        # Si no se encuentra como master, buscar por release
        release_search_url = f'{BASE_URL}database/search?q={query}&type=release&token={TOKEN}'
        response = requests.get(release_search_url, headers=HEADERS)
        release_results = response.json()

        if 'results' in release_results and release_results['results']:
            release_id = release_results['results'][0]['id']
            print(f'Encontrado como release: {release_id}')
            return

        # Si no se encuentra como release, buscar como artista
        artist_search_url = f'{BASE_URL}database/search?q={query}&type=artist&token={TOKEN}'
        response = requests.get(artist_search_url, headers=HEADERS)
        artist_results = response.json()

        if 'results' in artist_results and artist_results['results']:
            artist_id = artist_results['results'][0]['id']
            print(f'Encontrado como artista: {artist_id}')
            return

        print(f'No se encontraron resultados en Discogs para la consulta: {query}')

    except Exception as e:
        print(f'Error al realizar la búsqueda en Discogs: {str(e)}')

def main():
    parser = argparse.ArgumentParser(description='Search Discogs for artist, album, or track.')
    parser.add_argument('queries', nargs='+', type=str, help='Search query (artist, album, track)')
    args = parser.parse_args()

    # Combinar todos los argumentos en una sola cadena de búsqueda
    combined_query = ' '.join(args.queries)
    search_discogs(combined_query)

if __name__ == '__main__':
    main()