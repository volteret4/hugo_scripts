
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
    pattern = r"### Canciones\n\| Canción \| Artista \| Álbum \| Usuarios \|(.+?)(?=### Álbumes|\Z)"
    match = re.search(pattern, md_text, re.DOTALL)

    if not match:
        print("No se encontró la tabla de canciones.")
        return []

    canciones_data = []
    rows = match.group(1).strip().split("\n")
    for row in rows:
        columns = row.strip().split("|")
        if len(columns) >= 4:
            cancion = columns[1].strip()
            artista = columns[2].strip()
            album = columns[3].strip()
            usuarios = re.findall(r"([A-Za-z0-9_-]+) \((\d+)\)", columns[4].strip())
            usuarios = [(user, int(count)) for user, count in usuarios]
            canciones_data.append((cancion, artista, album, usuarios))
    
    print(f"Se extrajeron {len(canciones_data)} canciones.")
    return canciones_data

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
def plot_canciones(canciones_df, carpeta):
    configurar_graficos()
    
    # Primer gráfico: barras horizontales del total de escuchas
    plt.figure(figsize=(10, 12))
    canciones_df["Canción recortada"] = canciones_df["Canción"].apply(lambda x: recortar_texto(x, 30))
    plt.barh(canciones_df["Canción recortada"], canciones_df["Total escuchas"], color="#cba6f7")
    plt.xlabel("Número total de escuchas")
    plt.ylabel("Canción")
    plt.title("Canciones más compartidas")
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=10)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    guardar_grafico("canciones_bar.png", carpeta)
    plt.close()
    
    # Segundo gráfico: barras apiladas por usuario
    plt.figure(figsize=(12, len(canciones_df) * 0.5))
    bottom = np.zeros(len(canciones_df))
    
    # Obtener lista única de usuarios
    todos_usuarios = set()
    for usuarios in canciones_df["Usuarios"]:
        todos_usuarios.update(user for user, _ in usuarios)
    todos_usuarios = list(todos_usuarios)
    
    # Crear matriz de datos para el gráfico
    datos_usuarios = {usuario: [] for usuario in todos_usuarios}
    for usuarios in canciones_df["Usuarios"]:
        usuarios_dict = dict(usuarios)
        for usuario in todos_usuarios:
            datos_usuarios[usuario].append(usuarios_dict.get(usuario, 0))
    
    # Crear barras apiladas
    colores = plt.cm.Paired(np.linspace(0, 1, len(todos_usuarios)))
    for i, usuario in enumerate(todos_usuarios):
        plt.barh(range(len(canciones_df)), datos_usuarios[usuario], 
                left=bottom, label=usuario, color=colores[i])
        bottom += datos_usuarios[usuario]
    
    plt.yticks(range(len(canciones_df)), canciones_df["Canción recortada"])
    plt.xlabel("Número de escuchas por usuario")
    plt.title("Distribución de escuchas por usuario y canción")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    guardar_grafico("canciones_usuarios_bar.png", carpeta)
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
def procesar_datos(canciones_data, carpeta):
    if not canciones_data:
        print("No hay datos de canciones para procesar.")
        return

    canciones_df = pd.DataFrame(canciones_data, columns=["Canción", "Artista", "Álbum", "Usuarios"])

    # Convertimos la lista de tuplas en el número total de escuchas
    canciones_df["Total escuchas"] = canciones_df["Usuarios"].apply(lambda usuarios: sum([escuchas for _, escuchas in usuarios]))

    # Extraemos solo los nombres de usuario en un formato legible para graficar
    canciones_df["Usuarios completos"] = canciones_df["Usuarios"].apply(lambda usuarios: [f"{user} ({escuchas})" for user, escuchas in usuarios])

    print(canciones_df.head())
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    guardar_json(canciones_data, os.path.join(carpeta, "canciones_data.json"))

    # Generar los tres tipos de gráficos
    # 1. Gráficos de barras de canciones (incluye las barras apiladas por usuario)
    plot_canciones(canciones_df, carpeta)
    
    # 2. Gráfico de coincidencias entre usuarios
    plot_usuarios_coincidencias(canciones_df, carpeta)
    
    # 3. Gráficos circulares de cada canción
    #plot_pastel_canciones(canciones_df, carpeta)
    
    # Generate markdown with images
    generar_markdown_imagenes(carpeta, destino_md)


import os

def generar_markdown_imagenes(carpeta, destino_md):
    """
    Genera un archivo markdown con las imágenes organizadas según el formato especificado.
    """
    archivos = os.listdir(carpeta)
    archivos_png = [f for f in archivos if f.endswith('.png')]
    
    # Separar los archivos especiales de los gráficos circulares
    especiales = ['canciones_bar.png', 'usuarios_coincidencias.png']
    graficos_circulares = [f for f in archivos_png if f not in especiales]
    
    # Antes de abrir el archivo, leer el contenido actual y reemplazar 'ejemplo' con la variable destino_md
    if os.path.exists(destino_md):  # Si el archivo existe, reemplazar "ejemplo"
        with open(destino_md, "r", encoding='utf-8') as f:
            contenido = f.read()

        # Reemplazar "ejemplo" por el valor de destino_md
        contenido = contenido.replace("ejemplo", destino_md)
        contenido = contenido.replace("tag1", "grafico_canciones")

        # Escribir de nuevo el contenido modificado en el archivo
        with open(destino_md, "w", encoding='utf-8') as f:
            f.write(contenido)

    # Ahora, proceder con la parte de agregar los gráficos al archivo
    with open(destino_md, "a", encoding='utf-8') as f:
        # Primero escribimos los gráficos especiales
        for especial in especiales:
            if especial in archivos_png:
                nombre_sin_extension = os.path.splitext(especial)[0]
                f.write(f"![{nombre_sin_extension}](/rym/graficos/{carpeta_padre} {nombre_carpeta}/{especial})\n\n")
        
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
    archivo_md = sys.argv[1]    # archivo a leer para crear estadisticas
    carpeta = sys.argv[2]
    carpeta_padre = os.path.basename(os.path.dirname(carpeta))  # La carpeta padre
    nombre_carpeta = os.path.basename(carpeta)        # necesita ser /hugo/rym/static/graficos/FECHA/{CANCION|ALBUM|ARTISTA}
    destino_md = sys.argv[3]    # archivo markdown, debe estar en content/graficos/FECHa/{CANCION|ALBUM|ARTISTA}
    markdown_text = leer_markdown(archivo_md)
    canciones_data = extraer_tablas_canciones(markdown_text)
    procesar_datos(canciones_data, carpeta)