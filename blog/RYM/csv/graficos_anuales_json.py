import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from collections import defaultdict
import plotly.colors as colors

def load_and_process_data(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def create_top_songs_chart(data, output_path):
    # Procesar datos para encontrar las 30 canciones más compartidas
    song_users = defaultdict(set)
    song_plays = defaultdict(lambda: defaultdict(int))
    
    for user, user_data in data.items():
        for song in user_data:
            song_key = f"{song['name']} - {song['artist']['name']}"
            song_users[song_key].add(user)
            song_plays[song_key][user] += song['plays']
    
    # Ordenar por número de usuarios
    top_songs = sorted(song_users.items(), key=lambda x: len(x[1]), reverse=True)[:30]
    
    # Crear datos para el gráfico
    fig = go.Figure()
    
    for user in data.keys():
        user_plays = []
        for song, _ in top_songs:
            user_plays.append(song_plays[song][user])
        
        fig.add_trace(go.Bar(
            name=user,
            y=[song for song, _ in top_songs],
            x=user_plays,
            orientation='h'
        ))
    
    fig.update_layout(
        title='Top 30 Canciones Más Compartidas',
        barmode='stack',
        height=800,
        showlegend=True,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    fig.write_html(f"{output_path}/top_songs.html")

def create_genres_chart(data, output_path):
    # Similar al anterior pero para géneros
    # Asumiendo que los géneros están en los datos
    pass

def create_user_coincidences_chart(data, output_path):
    # Matriz de coincidencias entre usuarios
    users = list(data.keys())
    coincidences = defaultdict(int)
    
    for i, user1 in enumerate(users):
        for user2 in users[i+1:]:
            songs1 = {f"{song['name']} - {song['artist']['name']}" for song in data[user1]}
            songs2 = {f"{song['name']} - {song['artist']['name']}" for song in data[user2]}
            coincidences[f"{user1}-{user2}"] = len(songs1.intersection(songs2))
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(coincidences.keys()),
            y=list(coincidences.values())
        )
    ])
    
    fig.update_layout(
        title='Coincidencias Únicas entre Usuarios',
        xaxis_title='Pares de Usuarios',
        yaxis_title='Número de Coincidencias'
    )
    
    fig.write_html(f"{output_path}/user_coincidences.html")

def create_monthly_evolution(data, output_path):
    # Procesar timestamps para evolución mensual
    monthly_listens = defaultdict(lambda: defaultdict(int))
    
    for user, user_data in data.items():
        for song in user_data:
            for timestamp in song['timestamps']:
                month = datetime.fromtimestamp(timestamp).strftime('%Y-%m')
                monthly_listens[month][user] += 1
    
    # Crear DataFrame para visualización
    df = pd.DataFrame(monthly_listens).fillna(0)
    
    fig = px.line(
        df.T,
        title='Evolución de Escuchas por Usuario',
        labels={'index': 'Mes', 'value': 'Número de Escuchas'}
    )
    
    fig.write_html(f"{output_path}/monthly_evolution.html")

def main():
    # Configuración
    input_file = 'data.json'  # Ajusta según tu nombre de archivo
    output_path = 'static/charts'  # Carpeta en tu sitio Hugo
    
    # Cargar datos
    data = load_and_process_data(input_file)
    
    # Generar todos los gráficos
    create_top_songs_chart(data, output_path)
    #create_genres_chart(data, output_path)
    create_user_coincidences_chart(data, output_path)
    create_monthly_evolution(data, output_path)

if __name__ == "__main__":
    main()