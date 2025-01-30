import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import os
import math

def crear_grupos_canciones(df, canciones_por_grupo=10):
    """Divide el DataFrame en grupos de canciones"""
    return [df[i:i + canciones_por_grupo] for i in range(0, len(df), canciones_por_grupo)]

def generar_grafico_barras_grupo(grupo_df, numero_grupo, carpeta_salida):
    """Genera un gráfico de barras para un grupo de canciones"""
    # Crear figura con subplots: uno para barras totales y otro para barras apiladas
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Total de reproducciones', 'Reproducciones por usuario'),
        heights=[0.4, 0.6],
        vertical_spacing=0.1
    )

    # Configurar tema oscuro
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor='rgba(26, 26, 26, 1)',
        paper_bgcolor='rgba(26, 26, 26, 1)',
        height=800
    )

    # Gráfico de barras total
    fig.add_trace(
        go.Bar(
            x=grupo_df["Total escuchas"],
            y=grupo_df["Canción"],
            orientation='h',
            name='Total',
            marker_color='#cba6f7'
        ),
        row=1, col=1
    )

    # Gráfico de barras apiladas por usuario
    usuarios = set()
    for usuarios_lista in grupo_df["Usuarios"]:
        usuarios.update(user for user, _ in usuarios_lista)
    
    for usuario in usuarios:
        valores = []
        for usuarios_lista in grupo_df["Usuarios"]:
            dict_usuarios = dict(usuarios_lista)
            valores.append(dict_usuarios.get(usuario, 0))
        
        fig.add_trace(
            go.Bar(
                x=valores,
                y=grupo_df["Canción"],
                orientation='h',
                name=usuario
            ),
            row=2, col=1
        )

    # Configurar diseño
    fig.update_layout(
        title=f'Grupo {numero_grupo + 1} - Estadísticas de reproducciones',
        barmode='stack',
        showlegend=True,
        width=1200,
        height=800,
        font=dict(size=12),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.05
        )
    )

    # Guardar imagen
    nombre_archivo = f'grupo_{numero_grupo + 1}_canciones.png'
    ruta_archivo = os.path.join(carpeta_salida, nombre_archivo)
    fig.write_image(ruta_archivo)
    
    # Generar HTML para Markdown
    return f"![Grupo {numero_grupo + 1}](/rym/graficos/{os.path.basename(carpeta_salida)}/{nombre_archivo})\n\n"

def generar_heatmap_usuarios(df, carpeta_salida):
    """Genera un heatmap de coincidencias entre usuarios"""
    # Crear matriz de coincidencias
    coincidencias = {}
    usuarios_unicos = set()
    
    for usuarios in df["Usuarios"]:
        usuarios = [user for user, _ in usuarios]
        usuarios_unicos.update(usuarios)
        
        for i in range(len(usuarios)):
            for j in range(len(usuarios)):
                if i != j:
                    if usuarios[i] not in coincidencias:
                        coincidencias[usuarios[i]] = {}
                    if usuarios[j] not in coincidencias[usuarios[i]]:
                        coincidencias[usuarios[i]][usuarios[j]] = 0
                    coincidencias[usuarios[i]][usuarios[j]] += 1

    # Crear matriz para el heatmap
    usuarios_lista = list(usuarios_unicos)
    matriz_coincidencias = [[
        coincidencias.get(u1, {}).get(u2, 0) 
        for u2 in usuarios_lista
    ] for u1 in usuarios_lista]

    # Crear heatmap
    fig = go.Figure(data=go.Heatmap(
        z=matriz_coincidencias,
        x=usuarios_lista,
        y=usuarios_lista,
        colorscale='Viridis'
    ))

    fig.update_layout(
        title='Coincidencias entre usuarios',
        template="plotly_dark",
        plot_bgcolor='rgba(26, 26, 26, 1)',
        paper_bgcolor='rgba(26, 26, 26, 1)',
        width=800,
        height=800
    )

    # Guardar imagen
    nombre_archivo = 'heatmap_usuarios.png'
    ruta_archivo = os.path.join(carpeta_salida, nombre_archivo)
    fig.write_image(ruta_archivo)
    
    return f"![Heatmap usuarios](/rym/graficos/{os.path.basename(carpeta_salida)}/{nombre_archivo})\n\n"

def generar_markdown(df, carpeta_salida):
    """Genera todas las visualizaciones y el contenido Markdown"""
    if not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)

    contenido_md = "# Estadísticas de reproducciones\n\n"
    
    # Generar heatmap de usuarios
    contenido_md += "## Coincidencias entre usuarios\n\n"
    contenido_md += generar_heatmap_usuarios(df, carpeta_salida)
    
    # Generar gráficos por grupos
    grupos = crear_grupos_canciones(df)
    contenido_md += "## Estadísticas por grupos de canciones\n\n"
    
    for i, grupo in enumerate(grupos):
        contenido_md += generar_grafico_barras_grupo(grupo, i, carpeta_salida)
    
    return contenido_md

def procesar_visualizaciones(df, carpeta_salida, archivo_md_salida):
    """Función principal para procesar todas las visualizaciones"""
    contenido_md = generar_markdown(df, carpeta_salida)
    
    with open(archivo_md_salida, 'a', encoding='utf-8') as f:
        f.write(contenido_md)

# Ejemplo de uso:
# procesar_visualizaciones(df_canciones, 'ruta/carpeta/salida', 'ruta/archivo.md')