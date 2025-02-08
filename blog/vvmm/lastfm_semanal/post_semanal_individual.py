#!/usr/bin/env python3
import os
import subprocess
import datetime
import json
import yaml

class MusicBlogGenerator:
    def __init__(self, 
                 spotify_url_script_path, 
                 spotify_cover_script_path, 
                 hugo_blog_path):
        """
        Inicializa el generador de posts de música
        
        :param spotify_url_script_path: Ruta al script que obtiene URL de Spotify
        :param spotify_cover_script_path: Ruta al script que obtiene URL de carátula
        :param hugo_blog_path: Ruta al directorio raíz del blog Hugo
        """
        self.spotify_url_script = spotify_url_script_path
        self.spotify_cover_script = spotify_cover_script_path
        self.hugo_blog_path = hugo_blog_path
        
    def get_spotify_url(self, artist, album):
        """
        Obtiene la URL de Spotify para un artista y álbum
        
        :param artist: Nombre del artista
        :param album: Nombre del álbum
        :return: URL de Spotify
        """
        # Reemplazar espacios por guiones para los argumentos del script
        artist_arg = artist.replace(' ', '-')
        album_arg = album.replace(' ', '-')
        
        try:
            result = subprocess.run(
                [self.spotify_url_script, artist_arg, album_arg], 
                capture_output=True, 
                text=True, 
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error obteniendo URL de Spotify: {e}")
            return None
    
    def get_album_cover(self, spotify_url):
        """
        Obtiene la URL de la carátula del álbum
        
        :param spotify_url: URL de Spotify del álbum
        :return: URL de la carátula
        """
        try:
            result = subprocess.run(
                [self.spotify_cover_script, spotify_url], 
                capture_output=True, 
                text=True, 
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error obteniendo carátula: {e}")
            return None
    
    def get_weekly_listening_data(self):
        """
        Obtiene los datos de escuchas semanales (suponiendo un formato JSON)
        
        :return: Lista de álbumes ordenados por número de escuchas
        """
        # Método de ejemplo - deberás adaptarlo a tu fuente de datos
        # Por ejemplo, podrías leer un archivo JSON generado por Last.fm, 
        # Spotify Wrapped, o tu propio script de seguimiento
        try:
            with open('weekly_listening.json', 'r') as f:
                data = json.load(f)
                # Ordenar por número de escuchas de mayor a menor
                return sorted(data, key=lambda x: x['plays'], reverse=True)
        except FileNotFoundError:
            print("Archivo de escuchas no encontrado")
            return []
    
    def generate_hugo_post(self, albums):
        """
        Genera un post de Hugo con los álbumes de la semana
        
        :param albums: Lista de álbumes escuchados
        """
        # Generar nombre de archivo con fecha
        today = datetime.date.today()
        filename = f"{today.isocalendar()[0]}-W{today.isocalendar()[1]}-music-recap.md"
        filepath = os.path.join(
            self.hugo_blog_path, 
            'content', 
            'posts', 
            filename
        )
        
        # Preparar contenido del post
        frontmatter = {
            'title': f'Música de la Semana {today.isocalendar()[1]}',
            'date': today.isoformat(),
            'tags': ['música', 'semanal']
        }
        
        post_content = []
        for album in albums:
            spotify_url = self.get_spotify_url(album['artist'], album['album'])
            if spotify_url:
                cover_url = self.get_album_cover(spotify_url)
                post_content.append(
                    f"## {album['artist']} - {album['album']} (Reproducido {album['plays']} veces)\n\n"
                    f"[![Carátula]({cover_url})]({{spotify_url}})\n\n"
                )
        
        # Escribir archivo de post
        with open(filepath, 'w') as f:
            # Escribir frontmatter
            f.write('---\n')
            yaml.safe_dump(frontmatter, f, default_flow_style=False)
            f.write('---\n\n')
            
            # Escribir contenido
            f.write('\n'.join(post_content))
        
        print(f"Post generado: {filepath}")

def main():
    # Configuración - ajusta estas rutas según tu sistema
    generator = MusicBlogGenerator(
        spotify_url_script_path='/ruta/a/tu/script_url_spotify.sh',
        spotify_cover_script_path='/ruta/a/tu/script_cover.sh',
        hugo_blog_path='/ruta/a/tu/blog/hugo'
    )
    
    # Obtener datos de escuchas
    weekly_albums = generator.get_weekly_listening_data()
    
    # Generar post
    generator.generate_hugo_post(weekly_albums)

if __name__ == '__main__':
    main()