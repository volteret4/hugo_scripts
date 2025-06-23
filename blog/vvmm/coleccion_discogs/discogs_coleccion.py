import os
import shutil
from datetime import datetime
import discogs_client
from dotenv import load_dotenv
import subprocess

def formatear_nombre_archivo(artista, album):
    """
    Formatea el nombre del artista y álbum según el formato deseado
    """
    # Simplemente reemplazar espacios por guiones
    artista = artista.replace(' ', '-')
    album = album.replace(' ', '-')
    return f"{artista}-_-{album}"

def buscar_imagen(album, artista):
    """
    Busca imagen en las rutas posibles
    """
    nombre_archivo = formatear_nombre_archivo(artista, album)
    ruta_static = f'/home/pepe/hugo/web/vvmm/static/portadas/{nombre_archivo}.jpg'
    ruta_content = f'/home/pepe/hugo/web/vvmm/content/colecciones/images/{nombre_archivo}.jpg'
    
    if os.path.exists(ruta_static):
        return True, 'static', ruta_static
    elif os.path.exists(ruta_content):
        return True, 'content', ruta_content
    return False, None, None

def obtener_datos_discogs(username, token):
    """
    Obtiene los datos de la colección de Discogs
    """
    try:
        d = discogs_client.Client('MiColeccionScript/1.0', user_token=token)
        user = d.identity()
        
        datos_coleccion = []
        
        for item in user.collection_folders[0].releases:
            try:
                release = item.release
                
                datos_album = {
                    'album': release.title,
                    'artista': release.artists[0].name if release.artists else 'Desconocido',
                    'fecha_agregado': item.date_added.strftime('%Y-%m-%d'),
                    'generos': release.genres if hasattr(release, 'genres') else [],
                    'estilos': release.styles if hasattr(release, 'styles') else [],
                    'masterizado': '',
                    'ingeniero': '',
                    'productor': ''
                }
                
                # Verificar si la imagen ya existe
                imagen_existe, ubicacion, _ = buscar_imagen(datos_album['album'], datos_album['artista'])
                
                if not imagen_existe:
                    print(f"Descargando imagen para: {datos_album['artista']} - {datos_album['album']}")
                    try:
                        result = subprocess.run(
                            ["python3", "/home/pepe/Scripts/hugo_scripts/blog/vvmm/post/portadas/caratula-spotify.py", 
                             datos_album['artista'], datos_album['album']],
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        
                        if "Error" in result.stdout:
                            raise subprocess.CalledProcessError(1, result.args, result.stdout)
                        
                        print(f"Imagen descargada exitosamente")
                    except subprocess.CalledProcessError as e:
                        print(f"Error al ejecutar caratula-spotify.py: {e.stdout}")
                        print("Lanzando el script de respaldo...")
                        subprocess.run(
                            ["python3", "/home/pepe/Scripts/hugo_scripts/blog/vvmm/post/portadas/caratula-alternativa.py",
                             datos_album['artista'], datos_album['album'], 
                             "/home/pepe/hugo/web/vvmm/static/portadas/"]
                        )
                else:
                    print(f"Imagen ya existe en {ubicacion} para: {datos_album['artista']} - {datos_album['album']}")
                
                # Buscar información adicional en los créditos
                if hasattr(release, 'extraartists'):
                    for extra in release.extraartists:
                        if extra.role == 'Mastered By':
                            datos_album['masterizado'] = extra.name
                        elif extra.role == 'Engineer':
                            datos_album['ingeniero'] = extra.name
                        elif extra.role == 'Producer':
                            datos_album['productor'] = extra.name
                
                datos_coleccion.append(datos_album)
            except Exception as e:
                print(f"Error procesando un álbum: {e}")
        
        return datos_coleccion
    except Exception as e:
        print(f"Error al obtener datos de Discogs: {e}")
        return []

def generar_markdown(datos_coleccion, ruta_archivo):
    """
    Genera un único archivo markdown con toda la colección
    """
    fecha_hoy = datetime.today().strftime('%d-%m-%Y')
    carpeta_imagenes = f'/home/pepe/hugo/web/vvmm/static/portadas'
    os.makedirs(carpeta_imagenes, exist_ok=True)
    
    os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
    
    with open(ruta_archivo, 'w', encoding='utf-8') as f:
        f.write("---\n")
        f.write(f"title: \"Colección de Discos {fecha_hoy}\"\n")
        f.write(f"date: {datetime.today().strftime('%Y-%m-%d')}\n")
        f.write("tags:\n  - coleccion\n  - discogs\n")
        f.write("---\n\n")
        
        for album_data in datos_coleccion:
            nombre_archivo = formatear_nombre_archivo(album_data['artista'], album_data['album'])
            
            # Usar la función buscar_imagen mejorada
            imagen_existe, ubicacion, _ = buscar_imagen(album_data['album'], album_data['artista'])
            
            if imagen_existe:
                if ubicacion == 'static':
                    ruta_imagen_hugo = f"/portadas/{nombre_archivo}.jpg"
                else:
                    ruta_imagen_hugo = f"/images/{nombre_archivo}.jpg"
            else:
                ruta_imagen_hugo = ''
            
            # Separador inicial
            f.write("---\n")
            
            # Título: artista - album con la fecha
            f.write(f"{album_data['artista']} - {album_data['album']} {album_data['fecha_agregado']}\n\n")
            
            # Tabla con la imagen a la izquierda y el texto a la derecha
            f.write("| ![Portada](" + (ruta_imagen_hugo if ruta_imagen_hugo else '') + ") |")
            f.write(f" **Géneros:** {', '.join(album_data['generos']) if album_data['generos'] else 'N/A'} |")
            f.write(f" **Estilos:** {', '.join(album_data['estilos']) if album_data['estilos'] else 'N/A'} |\n")
            f.write("|--------------------------------------|------------------------------------|------------------------------------|\n")
            
            # Cerrar sección para este álbum
            f.write("\n")
def main():
    load_dotenv()
    
    TOKEN = os.getenv('DISCOGS_TOKEN')
    USERNAME = os.getenv('DISCOGS_USER')
    
    fecha_hoy = datetime.today().strftime('%d-%m-%Y')
    RUTA_ARCHIVO = f'/home/pepe/hugo/web/vvmm/content/coleccion/{fecha_hoy}.md'
    
    datos = obtener_datos_discogs(USERNAME, TOKEN)
    
    generar_markdown(datos, RUTA_ARCHIVO)
    
    print(f"Se ha generado un archivo markdown con {len(datos)} álbumes")

if __name__ == "__main__":
    main()