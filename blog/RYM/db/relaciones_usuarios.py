import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import networkx as nx
from pathlib import Path

class MusicAnalytics:
    def __init__(self, db_path, excluded_genres=None):
        self.db_path = db_path
        self.excluded_genres = set(g.lower() for g in (excluded_genres or []))
    
    def debug_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tablas en la base de datos:", [t[0] for t in tables])
        
        # Contar registros en cada tabla
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"Registros en {table[0]}: {count}")
            
        # Mostrar algunos ejemplos de cada tabla
        for table in tables:
            print(f"\nEjemplos de {table[0]}:")
            cursor.execute(f"SELECT * FROM {table[0]} LIMIT 3")
            print(cursor.fetchall())
        
        conn.close()

    def get_genre_data(self):
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT 
            u.username,
            g.name as genre,
            COUNT(p.id) as plays
        FROM users u
        JOIN plays p ON u.id = p.user_id
        JOIN tracks t ON p.track_id = t.id
        JOIN track_genres tg ON t.id = tg.track_id
        JOIN genres g ON tg.genre_id = g.id
        GROUP BY u.username, g.name
        HAVING plays > 0
        """
        
        df = pd.read_sql_query(query, conn)
        if self.excluded_genres:
            df = df[~df['genre'].str.lower().isin(self.excluded_genres)]
            
        print("\nEstructura del DataFrame:")
        print(df.info())
        print("\nPrimeras filas:")
        print(df.head())
        
        conn.close()
        return df

    def plot_top_genres(self, top_n=30, figsize=(12,8), dpi=300):
        df = self.get_genre_data()
        if df.empty:
            return None
            
        genre_total = df.groupby('genre')['plays'].sum().sort_values(ascending=True)
        top_genres = genre_total.tail(top_n)
        
        plt.figure(figsize=figsize, dpi=dpi)
        ax = top_genres.plot(kind='barh')
        
        for i, v in enumerate(top_genres):
            ax.text(v, i, f' {int(v):,}', va='center')
            
        plt.title(f"Top {top_n} Géneros más Escuchados")
        plt.xlabel("Total de Reproducciones")
        plt.tight_layout()
        return plt

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Uso: python script.py database.db output_dir")
        sys.exit(1)
    
    analyzer = MusicAnalytics(sys.argv[1])
    analyzer.debug_db()  # Primero debuggear la base de datos
    
    genres_plot = analyzer.plot_top_genres()
    if genres_plot:
        output_dir = sys.argv[2]
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        genres_plot.savefig(f"{output_dir}/top_genres.png", bbox_inches='tight')
        plt.close()