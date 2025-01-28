import re
import json
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
import numpy as np

def leer_markdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def extraer_tabla_artistas(md_text):
    pattern = r"### Artistas\n\| Artista \| Usuarios \|(.+?)(?=## Top 10|\Z)"
    match = re.search(pattern, md_text, re.DOTALL)
    if not match:
        print("No se encontró la tabla de artistas.")
        return []
    
    artists_data = []
    rows = match.group(1).strip().split("\n")
    for row in rows:
        if row.startswith('|') and not row.startswith('|-'):  # Ignorar la línea de separación
            columns = [col.strip() for col in row.split('|')[1:-1]]  # Eliminar columnas vacías al inicio y final
            if len(columns) >= 2:
                usuario = columns[0].strip()
                artista = columns[1].strip()
                artists_data.append((usuario, artista))
    
    print(f"Se extrajeron {len(artists_data)} entradas de artistas.")
    return artists_data

def configurar_graficos():
    plt.style.use("dark_background")
    plt.rcParams.update({
        "axes.facecolor": "#121212",
        "figure.facecolor": "#121212",
        "axes.labelcolor": "white",
        "xtick.color": "white",
        "ytick.color": "white",
        "text.color": "white",
    })

def recortar_texto(texto, max_chars=30):
    return texto[:max_chars] + "…" if len(texto) > max_chars else texto

def limpiar_nombre_archivo(nombre):
    chars_to_replace = ['&', '/', '\\', ':', '*', '?', '"', '<', '>', '|', '!', '%', '{', '}', '#', '@', '+', '=', '`', '$', "'"]
    for char in chars_to_replace:
        nombre = nombre.replace(char, '-')
    nombre = nombre.replace(' ', '-')
    while '--' in nombre:
        nombre = nombre.replace('--', '-')
    nombre = nombre.strip('-')
    return nombre

def guardar_grafico(nombre, carpeta):
    nombre_limpio = limpiar_nombre_archivo(nombre)
    path = os.path.join(carpeta, nombre_limpio)
    plt.savefig(path, dpi=150, bbox_inches='tight')
    print(f"Gráfico guardado: {path}")

def plot_artistas_populares(df, carpeta):
    configurar_graficos()
    
    # Contar frecuencia de artistas
    artistas_count = df['Artista'].value_counts()
    
    # Gráfico de barras de artistas más mencionados
    plt.figure(figsize=(12, 8))
    plt.barh(
        [recortar_texto(x) for x in artistas_count.index[:15]], 
        artistas_count.values[:15],
        color="#cba6f7"
    )
    plt.xlabel("Número de usuarios")
    plt.ylabel("Artista")
    plt.title("Artistas más escuchados")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    guardar_grafico("artistas_populares.png", carpeta)
    plt.close()

def plot_usuarios_activos(df, carpeta):
    configurar_graficos()
    
    # Contar artistas por usuario
    usuarios_count = df['Usuario'].value_counts()
    
    plt.figure(figsize=(12, 8))
    plt.barh(
        [recortar_texto(x) for x in usuarios_count.index], 
        usuarios_count.values,
        color="#94e2d5"
    )
    plt.xlabel("Número de artistas")
    plt.ylabel("Usuario")
    plt.title("Artistas por usuario")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    guardar_grafico("usuarios_activos.png", carpeta)
    plt.close()

def plot_usuarios_artistas_heatmap(df, carpeta):
    configurar_graficos()
    
    # Crear matriz de coincidencias entre usuarios
    pivot = pd.crosstab(df['Usuario'], df['Artista'])
    usuarios = pivot.index
    
    # Calcular coincidencias
    coincidencias = np.zeros((len(usuarios), len(usuarios)))
    for i in range(len(usuarios)):
        for j in range(len(usuarios)):
            coincidencias[i,j] = (pivot.iloc[i] & pivot.iloc[j]).sum()
    
    plt.figure(figsize=(12, 8))
    plt.imshow(coincidencias, cmap='Blues')
    plt.colorbar(label='Artistas en común')
    plt.xticks(range(len(usuarios)), usuarios, rotation=45, ha='right')
    plt.yticks(range(len(usuarios)), usuarios)
    plt.title("Coincidencias de artistas entre usuarios")
    plt.tight_layout()
    guardar_grafico("usuarios_coincidencias.png", carpeta)
    plt.close()

def procesar_datos(artists_data, carpeta):
    if not artists_data:
        print("No hay datos de artistas para procesar.")
        return
    
    # Crear DataFrame
    df = pd.DataFrame(artists_data, columns=["Usuario", "Artista"])
    print(df.head())
    
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    
    # Guardar datos en JSON
    guardar_json(artists_data, os.path.join(carpeta, "artists_data.json"))
    
    # Generar gráficos
    plot_artistas_populares(df, carpeta)
    plot_usuarios_activos(df, carpeta)
    plot_usuarios_artistas_heatmap(df, carpeta)

def guardar_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

def generar_markdown_imagenes(carpeta, destino_md):
    print(f"Generando markdown en: {destino_md}")
    
    os.makedirs(os.path.dirname(destino_md), exist_ok=True)
    
    archivos = os.listdir(carpeta)
    archivos_png = [f for f in archivos if f.endswith('.png')]
    print(f"Archivos PNG encontrados: {archivos_png}")
    
    especiales = ['artistas_populares.png', 'usuarios_activos.png', 'usuarios_coincidencias.png']
    
    if not os.path.exists(destino_md):
        with open(destino_md, "w", encoding='utf-8') as f:
            f.write(f"""+++
title = "Estadísticas de artistas"
date = {os.path.basename(os.path.dirname(os.path.dirname(destino_md)))}
draft = false
tags = ['artistas', 'graficos']
+++

""")
    
    with open(destino_md, "a", encoding='utf-8') as f:
        carpeta_padre = os.path.basename(os.path.dirname(carpeta))
        for especial in especiales:
            if especial in archivos_png:
                nombre_sin_extension = os.path.splitext(especial)[0]
                ruta_imagen = f"/rym/graficos/{fecha}/{codigo_fecha}/artistas/{especial}"
                linea_md = f"\n![{nombre_sin_extension}]({ruta_imagen})\n"
                print(f"Agregando imagen: {ruta_imagen}")
                f.write(linea_md)

if __name__ == "__main__":
    archivo_md = sys.argv[1]
    carpeta = sys.argv[2]
    # Divide la ruta en partes utilizando os.path.split
    partes = carpeta.split(os.sep)

    # Suponiendo que la estructura es siempre la misma, extraemos las partes deseadas
    fecha = partes[8]  # 'mensual'
    codigo_fecha = partes[9] 
    destino_md = sys.argv[3]
    
    print(f"Procesando archivo: {archivo_md}")
    print(f"Carpeta de salida: {carpeta}")
    print(f"Destino markdown: {destino_md}")
    
    markdown_text = leer_markdown(archivo_md)
    artists_data = extraer_tabla_artistas(markdown_text)
    procesar_datos(artists_data, carpeta)
    generar_markdown_imagenes(carpeta, destino_md)
    print("Proceso completado.")