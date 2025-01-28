
#!/usr/bin/env python
#
# Script Name: .py
# Description: 
# Author: volteret4
# Repository: https://github.com/volteret4/
# License:
# TODO: 
# Notes:
#   Dependencies:  - python3, 
#   Necesita 3 argumentos:   -path_archivo_markdown para leer
#                            -path_carpeta_salida graficos
#                            -path_archivo_salida_markdown

import re
import json
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
import numpy as np


# 1. Leer el archivo Markdown
def leer_markdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# 2. Extraer las tablas de canciones
def extraer_tablas_canciones(md_text):
    pattern = r"### Álbumes\n\| Álbum \| Artista \| Usuarios \|(.+?)(?=### Artistas|\Z)"
    match = re.search(pattern, md_text, re.DOTALL)
    if not match:
        print("No se encontró la tabla de álbumes.")
        return []
    
    albums_data = []
    rows = match.group(1).strip().split("\n")
    for row in rows:
        if row.startswith('|') and not row.startswith('|-'):  # Ignorar la línea de separación
            columns = [col.strip() for col in row.split('|')[1:-1]]  # Eliminar columnas vacías al inicio y final
            if len(columns) >= 3:
                album = columns[0].strip()
                artista = columns[1].strip()
                usuarios = re.findall(r"([A-Za-z0-9_-]+) \((\d+)\)", columns[2].strip())
                usuarios = [(user, int(count)) for user, count in usuarios]
                albums_data.append((album, artista, usuarios))
    
    print(f"Se extrajeron {len(albums_data)} álbumes.")
    return albums_data

# 3. Guardar JSON
def guardar_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

# 4. Configurar gráficos oscuros
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

def limpiar_nombre_archivo(nombre):
    """
    Limpia el nombre del archivo eliminando o reemplazando caracteres problemáticos.
    """
    # Caracteres a reemplazar por guion
    chars_to_replace = ['&', '/', '\\', ':', '*', '?', '"', '<', '>', '|', '!', '%', '{', '}', '#', '@', '+', '=', '`', '$', "'"]
    
    # Reemplazar caracteres problemáticos por guion
    for char in chars_to_replace:
        nombre = nombre.replace(char, '-')
    
    # Reemplazar los espacios por guiones
    nombre = nombre.replace(' ', '-')
    
    # Eliminar guiones múltiples
    while '--' in nombre:
        nombre = nombre.replace('--', '-')
    
    # Eliminar guiones al inicio y final
    nombre = nombre.strip('-')
    
    return nombre


def guardar_grafico(nombre, carpeta):
    """Guarda la imagen en la carpeta especificada, con nombre limpio."""
    nombre_limpio = limpiar_nombre_archivo(nombre)
    path = os.path.join(carpeta, nombre_limpio)
    # Configurar el tamaño de la figura (ancho, alto en pulgadas)
    #plt.figure(figsize=6,4)
    plt.savefig(path, dpi=150, bbox_inches='tight')
    print(f"Gráfico guardado: {path}")

def recortar_texto(texto, max_chars=30):
    """Recorta el texto si supera max_chars caracteres."""
    return texto[:max_chars] + "…" if len(texto) > max_chars else texto




# 5. Gráfico de barras de canciones
def plot_canciones(albums_df, carpeta):
    configurar_graficos()
    
    # Crear una columna que combine álbum y artista
    albums_df["Álbum_Artista"] = albums_df.apply(
        lambda x: f"{recortar_texto(x['Álbum'], 25)} - {recortar_texto(x['Artista'], 20)}", 
        axis=1
    )
    
    # Primer gráfico: barras horizontales del total de escuchas
    plt.figure(figsize=(12, 12))  # Aumentado el ancho para acomodar los nombres más largos
    plt.barh(albums_df["Álbum_Artista"], albums_df["Total escuchas"], color="#cba6f7")
    plt.xlabel("Número total de escuchas")
    plt.ylabel("Álbum - Artista")
    plt.title("Álbumes más compartidos")
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=10)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    guardar_grafico("albums_bar.png", carpeta)
    plt.close()
    
    # Segundo gráfico: barras apiladas por usuario
    plt.figure(figsize=(14, len(albums_df) * 0.5))  # Aumentado el ancho
    bottom = np.zeros(len(albums_df))
    
    todos_usuarios = set()
    for usuarios in albums_df["Usuarios"]:
        todos_usuarios.update(user for user, _ in usuarios)
    todos_usuarios = list(todos_usuarios)
    
    datos_usuarios = {usuario: [] for usuario in todos_usuarios}
    for usuarios in albums_df["Usuarios"]:
        usuarios_dict = dict(usuarios)
        for usuario in todos_usuarios:
            datos_usuarios[usuario].append(usuarios_dict.get(usuario, 0))
    
    colores = plt.cm.Paired(np.linspace(0, 1, len(todos_usuarios)))
    for i, usuario in enumerate(todos_usuarios):
        plt.barh(range(len(albums_df)), datos_usuarios[usuario], 
                left=bottom, label=usuario, color=colores[i])
        bottom += datos_usuarios[usuario]
    
    plt.yticks(range(len(albums_df)), albums_df["Álbum_Artista"])
    plt.xlabel("Número de escuchas por usuario")
    plt.title("Distribución de escuchas por usuario y álbum")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    guardar_grafico("albums_usuarios_bar.png", carpeta)
    plt.close()

# 6. Gráfico circular para cada canción
# def plot_pastel_canciones(canciones_df, carpeta):
#     configurar_graficos()
#     for _, row in canciones_df.iterrows():
#         usuarios = [user for user, count in row["Usuarios"]]
#         escuchas = [count for user, count in row["Usuarios"]]

#         if len(usuarios) > 1:
#             plt.figure(figsize=(8, 8))  # Aumenta el tamaño de la figura
            
#             # Configura etiquetas con los valores numéricos en lugar de porcentajes
#             etiquetas = [f"{user} ({count})" for user, count in row["Usuarios"]]

#             plt.pie(
#                 escuchas,
#                 labels=etiquetas,
#                 colors=plt.cm.Paired.colors,
#                 textprops={'fontsize': 30},  # Aumenta tamaño de fuente
#             )

#             plt.title(f'{row["Canción"]} - {row["Artista"]}', fontsize=40)  # Aumenta tamaño de título

#             # Generar nombre seguro para archivo
#             nombre_archivo = f"{row['Canción']} - {row['Artista']}.png".replace("/", "_").replace("\\", "_")
#             guardar_grafico(nombre_archivo, carpeta)
#             plt.close()

#     print("Gráficos circulares generados.")

# 7. Gráfico de coincidencias entre usuarios
def plot_usuarios_coincidencias(canciones_df, carpeta):
    configurar_graficos()
    
    # Crear diccionario de coincidencias
    coincidencias = {}
    
    # Obtener todos los usuarios únicos
    usuarios_unicos = set()
    for usuarios in canciones_df["Usuarios"]:
        usuarios = [user for user, _ in usuarios]
        usuarios_unicos.update(usuarios)
        
        # Contar coincidencias
        for i in range(len(usuarios)):
            for j in range(len(usuarios)):
                if i != j:
                    usuario1 = usuarios[i]
                    usuario2 = usuarios[j]
                    if usuario1 not in coincidencias:
                        coincidencias[usuario1] = {}
                    if usuario2 not in coincidencias[usuario1]:
                        coincidencias[usuario1][usuario2] = 0
                    coincidencias[usuario1][usuario2] += 1

    # Preparar datos para el gráfico
    usuarios = list(usuarios_unicos)
    totales = []
    coincidencias_por_usuario = []
    
    for usuario in usuarios:
        if usuario in coincidencias:
            total = sum(coincidencias[usuario].values())
            totales.append(total)
            coincidencias_por_usuario.append(coincidencias[usuario])
        else:
            totales.append(0)
            coincidencias_por_usuario.append({})

    # Ordenar usuarios por total de coincidencias
    usuarios_ordenados = [x for _, x in sorted(zip(totales, usuarios), reverse=True)]
    totales_ordenados = sorted(totales, reverse=True)
    coincidencias_ordenadas = []
    for usuario in usuarios_ordenados:
        if usuario in coincidencias:
            coincidencias_ordenadas.append(coincidencias[usuario])
        else:
            coincidencias_ordenadas.append({})

    # Crear gráfico
    plt.figure(figsize=(12, max(8, len(usuarios) * 0.4)))
    
    # Generar colores únicos para cada usuario
    colores = plt.cm.Paired(np.linspace(0, 1, len(usuarios)))
    color_map = dict(zip(usuarios_ordenados, colores))
    
    # Crear barras apiladas
    y_pos = np.arange(len(usuarios_ordenados))
    left = np.zeros(len(usuarios_ordenados))
    
    for usuario_coincide in usuarios_ordenados:
        valores = []
        for i, usuario_principal in enumerate(usuarios_ordenados):
            if usuario_principal in coincidencias and usuario_coincide in coincidencias[usuario_principal]:
                valores.append(coincidencias[usuario_principal][usuario_coincide])
            else:
                valores.append(0)
        plt.barh(y_pos, valores, left=left, label=usuario_coincide, 
                color=color_map[usuario_coincide])
        left += valores

    plt.yticks(y_pos, usuarios_ordenados)
    plt.xlabel("Número de coincidencias")
    plt.ylabel("Usuario")
    plt.title("Coincidencias entre usuarios")
    
    # Ajustar leyenda
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
              title="Coincide con")
    
    plt.tight_layout()
    guardar_grafico("usuarios_coincidencias.png", carpeta)  # Solo este guardar_grafico
    plt.close()

# 8. Procesar datos
def procesar_datos(albums_data, carpeta):
    if not albums_data:
        print("No hay datos de álbumes para procesar.")
        return
    
    albums_df = pd.DataFrame(albums_data, columns=["Álbum", "Artista", "Usuarios"])
    albums_df["Total escuchas"] = albums_df["Usuarios"].apply(lambda usuarios: sum([escuchas for _, escuchas in usuarios]))
    albums_df["Usuarios completos"] = albums_df["Usuarios"].apply(lambda usuarios: [f"{user} ({escuchas})" for user, escuchas in usuarios])
    
    print(albums_df.head())
    
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    
    guardar_json(albums_data, os.path.join(carpeta, "albums_data.json"))
    
    plot_canciones(albums_df, carpeta)
    plot_usuarios_coincidencias(albums_df, carpeta)
    generar_markdown_imagenes(carpeta, destino_md)


def generar_markdown_imagenes(carpeta, destino_md):
    """
    Genera un archivo markdown con las imágenes organizadas según el formato especificado.
    """
    print(f"Generando markdown en: {destino_md}")
    print(f"Buscando imágenes en: {carpeta}")
    
    # Asegurarse de que el directorio del archivo markdown existe
    os.makedirs(os.path.dirname(destino_md), exist_ok=True)
    
    archivos = os.listdir(carpeta)
    archivos_png = [f for f in archivos if f.endswith('.png')]
    print(f"Archivos PNG encontrados: {archivos_png}")
    
    # Archivos especiales que queremos incluir
    especiales = ['albums_bar.png', 'albums_usuarios_bar.png', 'usuarios_coincidencias.png']
    
    # Si el archivo no existe, crear uno con el contenido inicial
    if not os.path.exists(destino_md):
        print(f"Creando nuevo archivo markdown: {destino_md}")
        with open(destino_md, "w", encoding='utf-8') as f:
            f.write(f"""---
title: "Estadísticas de álbumes"
date: {os.path.basename(os.path.dirname(os.path.dirname(destino_md)))}
draft: false
tags: ['grafico_albums']
---

""")
    
    print("Escribiendo imágenes en el markdown...")
    with open(destino_md, "a", encoding='utf-8') as f:
        carpeta_padre = os.path.basename(os.path.dirname(carpeta))
        nombre_carpeta = os.path.basename(carpeta)
        
        for especial in especiales:
            if especial in archivos_png:
                nombre_sin_extension = os.path.splitext(especial)[0]
                ruta_imagen = f"/rym/graficos/{fecha}/{codigo_fecha}/albumes/{especial}"
                linea_md = f"\n![{nombre_sin_extension}]({ruta_imagen})\n"
                print(f"Agregando imagen: {ruta_imagen}")
                f.write(linea_md)
    
    print("Proceso de generación de markdown completado.")

        
        # # Tabla con los gráficos circulares
        # num_graficos = len(graficos_circulares)
        
        # f.write("| 1 | 2 | 3 | 4 |\n")
        # f.write("|---|---|---|---|\n")
        
        # for i in range(0, num_graficos, 4):
        #     fila_imagenes = []
        #     fila_nombres = []
            
        #     for j in range(4):
        #         if i + j < num_graficos:
        #             grafico = graficos_circulares[i + j]
        #             nombre_sin_extension = os.path.splitext(grafico)[0]
        #             fila_imagenes.append(f"![{nombre_sin_extension}](/rym/graficos/{os.path.basename(carpeta)}/{grafico})")
        #             nombre_formateado = nombre_sin_extension.replace('_', ' ')
        #             fila_nombres.append(nombre_formateado)
        #         else:
        #             fila_imagenes.append(" ")
        #             fila_nombres.append(" ")
            
        #     f.write(f"| {' | '.join(fila_imagenes)} |\n")
        #     f.write(f"| {' | '.join(fila_nombres)} |\n")



# 9. Ejecución
if __name__ == "__main__":
    archivo_md = sys.argv[1]
    carpeta = sys.argv[2]

    # Divide la ruta en partes utilizando os.path.split
    partes = carpeta.split(os.sep)

    # Suponiendo que la estructura es siempre la misma, extraemos las partes deseadas
    fecha = partes[8]  # 'mensual'
    codigo_fecha = partes[9]  # '01-24'
    
    destino_md = sys.argv[3]
    
    print(f"Procesando archivo: {archivo_md}")
    print(f"Carpeta de salida: {carpeta}")
    print(f"Destino markdown: {destino_md}")
    
    markdown_text = leer_markdown(archivo_md)
    albums_data = extraer_tablas_canciones(markdown_text)
    procesar_datos(albums_data, carpeta)
    
    # Llamada a la función para generar el markdown
    print("Generando archivo markdown con las imágenes...")
    generar_markdown_imagenes(carpeta, destino_md)
    print("Proceso completado.")