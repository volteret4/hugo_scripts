import tidalapi
import sys
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Acceder a las variables de entorno
TIDAL_USER = os.getenv('TIDAL_USER')
TIDAL_PWD = os.getenv('TIDAL_PWD')

# Verificar que las variables de entorno se cargaron correctamente
if not TIDAL_USER or not TIDAL_PWD:
    print("Error: Las variables de entorno TIDAL_USER y TIDAL_PWD deben estar definidas.")
    sys.exit(1)

def get_tidal_url(artist_name, album_name):
    session = tidalapi.Session()
    try:
        # Iniciar sesión en Tidal. Asegúrate de tener credenciales válidas
        session.login(TIDAL_USER, TIDAL_PWD)
    except requests.exceptions.HTTPError as e:
        print(f"Error al iniciar sesión en Tidal: {e}")
        return None

    search_results = session.search('artist', artist_name)
    artist = None
    for result in search_results.artists:
        if result.name.lower() == artist_name.lower():
            artist = result
            break

    if not artist:
        print(f"No se encontró el artista '{artist_name}' en Tidal.")
        return None

    search_results = session.search('album', album_name)
    album = None
    for result in search_results.albums:
        if result.artist.name.lower() == artist_name.lower() and result.name.lower() == album_name.lower():
            album = result
            break

    if not album:
        print(f"No se encontró el álbum '{album_name}' de '{artist_name}' en Tidal.")
        return None

    album_url = f"https://listen.tidal.com/album/{album.id}"
    return album_url

def main(artist, album):
    tidal_url = get_tidal_url(artist, album)
    if tidal_url:
        print(f"Enlace a Tidal para el álbum '{album}' de '{artist}': {tidal_url}")
    else:
        print(f"No se encontró un enlace a Tidal para el álbum '{album}' de '{artist}'.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python script.py 'Nombre del Artista' 'Nombre del Álbum'")
    else:
        artist = sys.argv[1]
        album = sys.argv[2]
        main(artist, album)