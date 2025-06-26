import requests
import argparse
import os
from dotenv import load_dotenv
import discogs_client
import musicbrainzngs
import urllib.parse
import time

# Cargar variables de entorno
load_dotenv()
home_dir = os.environ["HOME"]

DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN")
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

# Configurar APIs
musicbrainzngs.set_useragent("PortadaDownloader", "1.0", "your-email@example.com")
if DISCOGS_TOKEN:
    discogs = discogs_client.Client('PortadaDownloader/1.0', user_token=DISCOGS_TOKEN)
else:
    discogs = None


def validar_url_imagen(url):
    """Verifica que la URL de imagen sea válida y accesible."""
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            return content_type.startswith('image/')
        return False
    except Exception as e:
        print(f"Error validando URL {url}: {e}")
        return False


def buscar_portada_musicbrainz(artista, album):
    """Busca la URL de la portada en MusicBrainz."""
    try:
        print(f"  → Buscando '{artista} - {album}' en MusicBrainz...")
        resultados = musicbrainzngs.search_releases(artist=artista, release=album, limit=5)
        
        if resultados['release-list']:
            for release in resultados['release-list']:
                release_id = release['id']
                cover_url = f"https://coverartarchive.org/release/{release_id}/front"
                
                print(f"  → Verificando: {cover_url}")
                if validar_url_imagen(cover_url):
                    return cover_url
                    
        print("  → No se encontró portada válida en MusicBrainz")
        return None
    except Exception as e:
        print(f"  → Error buscando en MusicBrainz: {e}")
        return None


def buscar_portada_discogs(artista, album):
    """Busca la URL de la portada en Discogs."""
    if not discogs:
        print("  → Token de Discogs no configurado")
        return None
        
    try:
        print(f"  → Buscando '{artista} - {album}' en Discogs...")
        # Buscar de diferentes maneras
        queries = [
            f"{artista} {album}",
            f"{artista} - {album}",
            album
        ]
        
        for query in queries:
            try:
                results = discogs.search(query, type='release')
                if results:
                    for release in results[:3]:  # Revisar los primeros 3 resultados
                        try:
                            # Obtener detalles completos del release
                            full_release = discogs.release(release.id)
                            if hasattr(full_release, 'images') and full_release.images:
                                image_url = full_release.images[0]['uri']
                                print(f"  → Verificando: {image_url}")
                                if validar_url_imagen(image_url):
                                    return image_url
                        except Exception as e:
                            print(f"  → Error procesando release {release.id}: {e}")
                            continue
                            
                time.sleep(1)  # Respetar límites de la API
            except Exception as e:
                print(f"  → Error en búsqueda '{query}': {e}")
                continue
                
        print("  → No se encontró portada válida en Discogs")
        return None
    except Exception as e:
        print(f"  → Error buscando en Discogs: {e}")
        return None


def buscar_portada_lastfm(artista, album):
    """Busca la URL de la portada en Last.fm."""
    if not LASTFM_API_KEY:
        print("  → API key de Last.fm no configurada")
        return None
        
    try:
        print(f"  → Buscando '{artista} - {album}' en Last.fm...")
        
        # URL encode de los parámetros
        artista_encoded = urllib.parse.quote(artista)
        album_encoded = urllib.parse.quote(album)
        
        url = f"http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key={LASTFM_API_KEY}&artist={artista_encoded}&album={album_encoded}&format=json"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            if 'album' in data and 'image' in data['album']:
                images = data['album']['image']
                # Buscar la imagen de mayor resolución
                for img in reversed(images):
                    if img.get('#text') and img['#text'].strip():
                        image_url = img['#text']
                        print(f"  → Verificando: {image_url}")
                        if validar_url_imagen(image_url):
                            return image_url
            else:
                print(f"  → No hay datos de álbum en la respuesta: {data}")
        else:
            print(f"  → Error HTTP {response.status_code}: {response.text}")
            
        print("  → No se encontró portada válida en Last.fm")
        return None
    except Exception as e:
        print(f"  → Error buscando en Last.fm: {e}")
        return None


def descargar_portada(artista, album, url, ruta_salida):
    """Descarga y guarda la portada en la ruta especificada."""
    try:
        print(f"Descargando desde: {url}")
        
        # Headers para evitar bloqueos
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, stream=True, headers=headers, timeout=30)
        if response.status_code == 200:
            # Limpiar nombre de archivo
            nombre_archivo = f"{artista} - {album}".replace(' ', '_')
            nombre_archivo = "".join(c for c in nombre_archivo if c.isalnum() or c in ('_', '-', '.')).rstrip()
            
            # Determinar extensión basándose en el content-type
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                extension = '.jpg'
            elif 'png' in content_type:
                extension = '.png'
            elif 'webp' in content_type:
                extension = '.webp'
            else:
                extension = '.jpg'  # Por defecto
            
            # Construir ruta completa
            ruta_archivo = os.path.join(ruta_salida, f"{nombre_archivo}{extension}")
            
            # Crear directorio si no existe
            os.makedirs(ruta_salida, exist_ok=True)
            
            with open(ruta_archivo, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)

            print(f"✓ Portada guardada en: {ruta_archivo}")
            return True
        else:
            print(f"✗ Error al descargar portada: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error descargando portada: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Descarga la portada de un álbum desde varias fuentes.")
    parser.add_argument("artista", help="Nombre del artista.")
    parser.add_argument("album", help="Nombre del álbum.")
    parser.add_argument("ruta", help="Ruta donde guardar la portada.")
    parser.add_argument("--debug", action="store_true", help="Mostrar información de debug.")
    args = parser.parse_args()

    print(f"Buscando portada para: {args.artista} - {args.album}")
    print(f"Ruta de salida: {args.ruta}")
    print("-" * 50)

    # Verificar que las APIs estén configuradas
    if args.debug:
        print(f"DISCOGS_TOKEN: {'✓' if DISCOGS_TOKEN else '✗'}")
        print(f"LASTFM_API_KEY: {'✓' if LASTFM_API_KEY else '✗'}")
        print("-" * 50)

    # Intentar cada fuente en orden hasta que una funcione
    fuentes = [
        ('Last.fm', buscar_portada_lastfm),
        ('MusicBrainz', buscar_portada_musicbrainz),
        ('Discogs', buscar_portada_discogs)
    ]

    for nombre_fuente, buscar_funcion in fuentes:
        print(f"\n🔍 Buscando en {nombre_fuente}...")
        portada_url = buscar_funcion(args.artista, args.album)
        
        if portada_url:
            print(f"✓ Portada encontrada en {nombre_fuente}")
            if descargar_portada(args.artista, args.album, portada_url, args.ruta):
                print(f"\n🎉 ¡Descarga completada exitosamente!")
                break
            else:
                print(f"✗ Falló la descarga, intentando siguiente fuente...")
    else:
        print("\n😞 No se pudo encontrar o descargar la portada de ninguna fuente.")
        print("\nConsejos para mejorar los resultados:")
        print("- Verifica que el artista y álbum estén escritos correctamente")
        print("- Prueba variaciones del nombre (con/sin artículos, etc.)")
        print("- Asegúrate de tener configuradas las API keys en el archivo .env")


if __name__ == "__main__":
    main()