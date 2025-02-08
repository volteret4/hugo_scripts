
# #!/usr/bin/env python
# #
# # Script Name: .py
# # Description: 
# # Author: volteret4
# # Repository: https://github.com/volteret4/
# # License:
# # TODO: 
# # Notes:
# #   Dependencies:  - python3, 
# #
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import json
from typing import Dict, List, Optional
import argparse

class LastFMVisualizer:
    def __init__(self, output_dir: str = 'visualizations'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración global de estilo
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
        plt.rcParams['figure.figsize'] = [12, 8]
        plt.rcParams['figure.dpi'] = 300

    def load_data(self, filepath: Path) -> Dict:
        """Carga datos de un archivo JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_plot(self, name: str):
        """Guarda el plot actual"""
        plt.tight_layout()
        output_path = self.output_dir / f"{name}.png"
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        print(f"Gráfico guardado en: {output_path}")

    def plot_user_similarity_network(self, coincidences_file: Path):
        """Crea un gráfico de red mostrando similitudes entre usuarios"""
        data = self.load_data(coincidences_file)
        
        # Extraer usuarios y coincidencias
        users = data['metadata']['users']
        matrix_size = len(users)
        similarity_matrix = np.zeros((matrix_size, matrix_size))
        
        # Calcular similitudes basadas en artistas
        for i, user1 in enumerate(users):
            for j, user2 in enumerate(users):
                if i < j:  # Solo procesar la mitad superior de la matriz
                    pair_key = f"{user1}-{user2}"
                    common_artists = len(data['artists'].get(pair_key, []))
                    similarity_matrix[i, j] = common_artists
                    similarity_matrix[j, i] = common_artists  # Matriz simétrica

        plt.figure(figsize=(10, 10))
        sns.heatmap(similarity_matrix,
                   xticklabels=users,
                   yticklabels=users,
                   cmap='YlOrRd',
                   annot=True,
                   fmt='g')
        plt.title('Red de Similitud entre Usuarios')
        self.save_plot('user_similarity_network')

    def plot_genre_comparison(self, year_files: List[Path]):
        """Compara géneros entre usuarios"""
        genre_data = []
        for file in year_files:
            data = self.load_data(file)
            # Extraer username de la estructura correcta del JSON
            username = data.get('annual', {}).get('user', {}).get('name', Path(file).stem)
            
            if 'annual' in data and 'top_artists' in data['annual']:
                artists = data['annual']['top_artists'].get('topartists', {}).get('artist', [])
                for artist in artists:
                    if isinstance(artist, dict) and 'tags' in artist:
                        for tag in artist['tags'][:3]:
                            genre_data.append({
                                'Usuario': username,
                                'Genre': tag['name'],
                                'Plays': int(artist['playcount'])
                            })
        
        if not genre_data:
            print("No se encontraron datos de géneros")
            return
            
        df = pd.DataFrame(genre_data)
        top_genres = df.groupby('Genre')['Plays'].sum().nlargest(10).index
        
        plt.figure(figsize=(15, 8))
        df_filtered = df[df['Genre'].isin(top_genres)]
        
        sns.barplot(data=df_filtered,
                   x='Genre',
                   y='Plays',
                   hue='Usuario')
        plt.xticks(rotation=45, ha='right')
        plt.title('Comparación de Géneros entre Usuarios')
        self.save_plot('genre_comparison')


   
    def plot_listening_trends(self, year_files: List[Path]):
        """Muestra tendencias de escucha a lo largo del año"""
        trends_data = []
        for file in year_files:
            data = self.load_data(file)
            username = data.get('annual', {}).get('user', {}).get('name', Path(file).stem)
            
            for month, month_data in data.get('monthly', {}).items():
                if 'top_tracks' in month_data:
                    tracks = month_data['top_tracks'].get('toptracks', {}).get('track', [])
                    total_plays = sum(int(track.get('playcount', 0)) for track in tracks)
                    trends_data.append({
                        'Usuario': username,
                        'Month': pd.to_datetime(month).strftime('%Y-%m'),
                        'Plays': total_plays
                    })
        
        if not trends_data:
            print("No se encontraron datos de tendencias")
            return
            
        df = pd.DataFrame(trends_data)
        plt.figure(figsize=(15, 6))
        sns.lineplot(data=df,
                    x='Month',
                    y='Plays',
                    hue='Usuario',
                    marker='o')
        plt.xticks(rotation=45)
        plt.title('Tendencias de Escucha por Usuario')
        self.save_plot('listening_trends')

    def plot_obsession_comparison(self, year_files: List[Path]):
        """Compara niveles de obsesión musical entre usuarios"""
        obsession_data = []
        for file in year_files:
            data = self.load_data(file)
            username = data.get('annual', {}).get('user', {}).get('name', Path(file).stem)
            
            if 'annual' in data and 'top_tracks' in data['annual']:
                tracks = data['annual']['top_tracks'].get('toptracks', {}).get('track', [])
                if tracks:
                    playcounts = [int(track.get('playcount', 0)) for track in tracks]
                    mean = np.mean(playcounts)
                    std = np.std(playcounts)
                    
                    for track in tracks[:10]:
                        playcount = int(track.get('playcount', 0))
                        if std != 0:
                            z_score = (playcount - mean) / std
                            obsession_data.append({
                                'Usuario': username,
                                'Track': f"{track.get('name', '')} - {track.get('artist', {}).get('name', '')}",
                                'Level': z_score
                            })
        
        if not obsession_data:
            print("No se encontraron datos de obsesiones")
            return
            
        df = pd.DataFrame(obsession_data)
        top_obsessions = df.nlargest(15, 'Level')
        
        plt.figure(figsize=(15, 8))
        sns.barplot(data=top_obsessions,
                   x='Track',
                   y='Level',
                   hue='Usuario')
        plt.xticks(rotation=45, ha='right')
        plt.title('Comparación de Obsesiones Musicales (Z-Score)')
        self.save_plot('obsession_comparison')


    def plot_top_shared_artists(self, coincidences_file: Path, top_n: int = 30):
        """Visualiza los artistas más compartidos entre usuarios con desglose por usuario"""
        data = self.load_data(coincidences_file)
        
        # Crear un diccionario para almacenar qué usuarios escuchan cada artista
        artist_by_user = {}
        users = data['metadata']['users']
        
        # Procesar coincidencias para obtener qué usuarios escuchan cada artista
        for pair, artists in data['artists'].items():
            user1, user2 = pair.split('-')
            for artist in artists:
                if artist not in artist_by_user:
                    artist_by_user[artist] = set()
                artist_by_user[artist].add(user1)
                artist_by_user[artist].add(user2)
        
        # Ordenar artistas por número total de usuarios
        sorted_artists = sorted(artist_by_user.items(), 
                              key=lambda x: len(x[1]), 
                              reverse=True)[:top_n]
        
        # Preparar datos para el gráfico
        plot_data = []
        for artist, user_set in sorted_artists:
            for user in users:
                plot_data.append({
                    'Artist': artist,
                    'Usuario': user,
                    'Count': 1 if user in user_set else 0
                })
        
        df = pd.DataFrame(plot_data)
        
        # Crear el gráfico
        plt.figure(figsize=(20, 10))
        sns.barplot(data=df,
                   x='Artist',
                   y='Count',
                   hue='Usuario')
        
        plt.xticks(rotation=45, ha='right')
        plt.title(f'Top {top_n} Artistas Compartidos (Desglosado por Usuario)')
        plt.legend(title='Usuario', bbox_to_anchor=(1.05, 1), loc='upper left')
        self.save_plot('shared_artists')

def main():
    parser = argparse.ArgumentParser(description='Visualizador de datos de LastFM')
    parser.add_argument('--data-dir', type=str, required=True,
                       help='Directorio con los datos')
    parser.add_argument('--output-dir', type=str, default='visualizations',
                       help='Directorio para guardar las visualizaciones')
    parser.add_argument('--plots', nargs='+', choices=[
        'similarity', 'genres', 'trends', 'shared', 'obsessions'
    ], help='Gráficos a generar')
    
    args = parser.parse_args()
    
    visualizer = LastFMVisualizer(args.output_dir)
    data_dir = Path(args.data_dir)
    
    try:
        if 'similarity' in args.plots:
            coincidences_files = list(data_dir.glob('**/coincidences*.json'))
            if coincidences_files:
                visualizer.plot_user_similarity_network(coincidences_files[0])
            else:
                print("No se encontró archivo de coincidencias")
        
        if 'genres' in args.plots:
            year_files = list(data_dir.glob('**/*_20*.json'))
            if year_files:
                visualizer.plot_genre_comparison(year_files)
            else:
                print("No se encontraron archivos de datos anuales")
        
        if 'trends' in args.plots:
            year_files = list(data_dir.glob('**/*_20*.json'))
            if year_files:
                visualizer.plot_listening_trends(year_files)
            else:
                print("No se encontraron archivos de datos anuales")
        
        if 'shared' in args.plots:
            coincidences_files = list(data_dir.glob('**/coincidences*.json'))
            if coincidences_files:
                visualizer.plot_top_shared_artists(coincidences_files[0])
            else:
                print("No se encontró archivo de coincidencias")
        
        if 'obsessions' in args.plots:
            year_files = list(data_dir.glob('**/*_20*.json'))
            if year_files:
                visualizer.plot_obsession_comparison(year_files)
            else:
                print("No se encontraron archivos de datos anuales")
                
    except Exception as e:
        print(f"Error durante la visualización: {e}")

if __name__ == "__main__":
    main()