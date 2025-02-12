import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
from typing import Tuple, List
import numpy as np
from datetime import datetime, timedelta

class MusicVisualization:
    def __init__(self, db_path: str, output_path: str):
        self.conn = sqlite3.connect(db_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        plt.style.use('seaborn-v0_8-deep')
        sns.set_palette("husl")
    
    def get_date_filter(self, period: str, date: str) -> Tuple[str, tuple]:
        """
        Genera la cláusula WHERE SQL basada en el período y fecha
        Params:
            period: 'semanal', 'mensual', o 'anual'
            date: número de semana (1-53), mes (1-12), o año (YYYY)
        """
        current_date = datetime.now()
        
        if period == "semanal":
            # Convertir número de semana a rango de fechas
            year = current_date.year
            week = int(date)
            start_date = datetime.strptime(f'{year}-W{week}-1', '%Y-W%W-%w')
            end_date = start_date + timedelta(days=7)
            return """
                datetime(timestamp, 'unixepoch') >= datetime(?, 'start of day')
                AND datetime(timestamp, 'unixepoch') < datetime(?, 'start of day')
            """, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            
        elif period == "mensual":
            # Convertir número de mes a rango de fechas
            year = current_date.year
            month = int(date)
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            return """
                datetime(timestamp, 'unixepoch') >= datetime(?, 'start of day')
                AND datetime(timestamp, 'unixepoch') < datetime(?, 'start of day')
            """, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            
        else:  # anual
            year = int(date)
            start_date = f"{year}-01-01"
            end_date = f"{year + 1}-01-01"
            return """
                datetime(timestamp, 'unixepoch') >= datetime(?, 'start of day')
                AND datetime(timestamp, 'unixepoch') < datetime(?, 'start of day')
            """, (start_date, end_date)

    def user_coincidences(self, period: str, date: str) -> None:
        """
        Genera gráfico de barras de coincidencias entre usuarios
        """
        where_clause, params = self.get_date_filter(period, date)
        
        query = f"""
        WITH user_songs AS (
            SELECT DISTINCT username, song_name, artist_name
            FROM songs s
            WHERE {where_clause}
        ),
        user_pairs AS (
            SELECT 
                a.username as user1,
                b.username as user2,
                COUNT(*) as coincidences
            FROM user_songs a
            JOIN user_songs b ON a.song_name = b.song_name 
                AND a.artist_name = b.artist_name
                AND a.username < b.username
            GROUP BY a.username, b.username
        )
        SELECT * FROM user_pairs
        ORDER BY coincidences DESC
        """
        
        df = pd.read_sql_query(query, self.conn, params=params)
        
        if df.empty:
            print("No hay coincidencias para este período")
            return
            
        plt.figure(figsize=(12, 6))
        bars = plt.bar(
            df.apply(lambda x: f"{x['user1']} - {x['user2']}", axis=1),
            df['coincidences']
        )
        
        colors = sns.color_palette("husl", len(bars))
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        plt.xticks(rotation=45, ha='right')
        plt.title(f'Coincidencias entre usuarios ({period} - {date})')
        plt.xlabel('Pares de usuarios')
        plt.ylabel('Número de coincidencias')
        
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2.,
                height,
                f'{int(height)}',
                ha='center', va='bottom'
            )
        
        plt.tight_layout()
        plt.savefig(self.output_path / f'user_coincidences_{period}_{date}.png')
        plt.close()

    def album_coincidences(self, period: str, date: str) -> None:
        """
        Genera un heatmap de coincidencias de álbumes entre usuarios
        """
        where_clause, params = self.get_date_filter(period, date)
        
        query = f"""
        WITH common_albums AS (
            SELECT DISTINCT 
                a.username as user1,
                b.username as user2,
                a.song_name,
                a.artist_name
            FROM songs a
            JOIN songs b ON a.song_name = b.song_name 
                AND a.artist_name = b.artist_name
                AND a.username < b.username
            WHERE ({where_clause})
        )
        SELECT 
            user1, user2,
            GROUP_CONCAT(artist_name || ' - ' || song_name) as songs,
            COUNT(*) as count
        FROM common_albums
        GROUP BY user1, user2
        """
        
        df = pd.read_sql_query(query, self.conn, params=params)
        
        if df.empty:
            print("No hay coincidencias de álbumes para este período")
            return
        
        users = sorted(list(set(df['user1'].unique()) | set(df['user2'].unique())))
        matrix = pd.DataFrame(0, index=users, columns=users)
        
        for _, row in df.iterrows():
            matrix.loc[row['user1'], row['user2']] = row['count']
            matrix.loc[row['user2'], row['user1']] = row['count']
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(
            matrix,
            annot=True,
            cmap='YlOrRd',
            fmt='g',
            cbar_kws={'label': 'Número de coincidencias'}
        )
        
        plt.title(f'Coincidencias de álbumes entre usuarios ({period} - {date})')
        plt.tight_layout()
        plt.savefig(self.output_path / f'album_coincidences_{period}_{date}.png')
        plt.close()

    def top_common_items(self, period: str, date: str) -> None:
        """
        Genera gráfico horizontal de los elementos más coincididos entre todos los usuarios
        """
        where_clause, params = self.get_date_filter(period, date)
        
        query = f"""
        WITH user_counts AS (
            SELECT 
                artist_name,
                song_name,
                COUNT(DISTINCT username) as user_count
            FROM songs s
            WHERE {where_clause}
            GROUP BY artist_name, song_name
            HAVING user_count > 1
        )
        SELECT 
            artist_name || ' - ' || song_name as item,
            user_count
        FROM user_counts
        ORDER BY user_count DESC
        LIMIT 15
        """
        
        df = pd.read_sql_query(query, self.conn, params=params)
        
        if df.empty:
            print("No hay elementos comunes para este período")
            return
        
        plt.figure(figsize=(12, 8))
        bars = plt.barh(df['item'], df['user_count'])
        
        colors = sns.color_palette("husl", len(bars))
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        plt.title(f'Top canciones compartidas entre usuarios ({period} - {date})')
        plt.xlabel('Número de usuarios que comparten')
        plt.ylabel('Canción')
        
        for bar in bars:
            width = bar.get_width()
            plt.text(
                width,
                bar.get_y() + bar.get_height()/2.,
                f'{int(width)}',
                ha='left', va='center'
            )
        
        plt.tight_layout()
        plt.savefig(self.output_path / f'top_common_{period}_{date}.png')
        plt.close()

    def generate_all_visualizations(self, period: str, date: str) -> None:
        """
        Genera todas las visualizaciones
        """
        self.user_coincidences(period, date)
        self.album_coincidences(period, date)
        self.top_common_items(period, date)
        
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    parser = argparse.ArgumentParser(description='Genera visualizaciones para el blog de música')
    parser.add_argument('output_path', help='Carpeta de destino para las imágenes')
    parser.add_argument('db_path', help='Ruta a la base de datos SQLite')
    parser.add_argument('period', choices=['semanal', 'mensual', 'anual'], help='Período de tiempo')
    parser.add_argument('date', help='Fecha específica (número de semana 1-53, mes 1-12, o año YYYY)')
    
    args = parser.parse_args()
    
    viz = MusicVisualization(args.db_path, args.output_path)
    viz.generate_all_visualizations(args.period, args.date)

if __name__ == "__main__":
    main()