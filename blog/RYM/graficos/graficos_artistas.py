import re
import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams
import sys
import os
import numpy as np
from matplotlib.font_manager import FontProperties, fontManager
import unicodedata




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
def configurar_fuentes():
    """
    Configura las fuentes del sistema según el sistema operativo,
    con fallbacks para caracteres CJK
    """
    sistema = platform.system()
    
    if sistema == 'Linux':
        fuentes_candidatas = [
            'Noto Sans CJK JP',
            'Noto Sans CJK',
            'Noto Sans',
            'DejaVu Sans',
            'Ubuntu',
            'Liberation Sans'
        ]
    elif sistema == 'Windows':
        fuentes_candidatas = [
            'Yu Gothic',
            'Meiryo',
            'MS Gothic',
            'Arial Unicode MS',
            'Arial'
        ]
    elif sistema == 'Darwin':  # macOS
        fuentes_candidatas = [
            'Hiragino Sans GB',
            'Hiragino Kaku Gothic Pro',
            'Apple SD Gothic Neo',
            'Arial Unicode MS'
        ]
    else:
        fuentes_candidatas = ['DejaVu Sans']

    # Intentar encontrar una fuente disponible
    fuente_encontrada = None
    for fuente in fuentes_candidatas:
        try:
            font_prop = FontProperties(family=fuente)
            if font_prop.get_name() != 'DejaVu Sans':  # Si encontró la fuente
                fuente_encontrada = fuente
                break
        except:
            continue
    
    if fuente_encontrada is None:
        print("Advertencia: No se encontró una fuente con soporte CJK. Usando DejaVu Sans.")
        fuente_encontrada = 'DejaVu Sans'
    
    return fuente_encontrada
    
def sanitizar_texto(texto):
    """
    Limpia el texto reemplazando caracteres problemáticos con sus equivalentes ASCII
    o removiéndolos si no hay equivalente
    """
    # Primero intentamos una transliteración básica
    texto_limpio = ''
    for char in texto:
        # Si es un carácter ASCII, lo mantenemos
        if ord(char) < 128:
            texto_limpio += char
        else:
            # Para caracteres no-ASCII, intentamos encontrar una representación ASCII
            try:
                nombre = unicodedata.name(char)
                if 'CJK' in nombre or 'HIRAGANA' in nombre or 'KATAKANA' in nombre:
                    texto_limpio += '_'  # Reemplazar caracteres CJK con guión bajo
                else:
                    # Intentar normalizar a ASCII
                    texto_limpio += unicodedata.normalize('NFKD', char).encode('ASCII', 'ignore').decode()
            except:
                texto_limpio += '_'
    
    return texto_limpio

def listar_fuentes_disponibles():
    """
    Lista todas las fuentes disponibles en el sistema
    """
    fuentes = [f.name for f in fontManager.ttflist]
    print("Fuentes disponibles:", fuentes)
    return fuentes

def configurar_graficos():
    plt.style.use("dark_background")
    
    # Primero listamos las fuentes disponibles para diagnóstico
    fuentes_disponibles = listar_fuentes_disponibles()
    
    # Intentamos usar Liberation Sans como fuente principal
    if 'Liberation Sans' in fuentes_disponibles:
        fuente_principal = 'Liberation Sans'
    else:
        print("Liberation Sans no encontrada, usando fuente por defecto")
        fuente_principal = 'DejaVu Sans'
    
    custom_colors = {
        'background': '#1a1b26',
        'text': '#c0caf5',
        'grid': '#292e42',
        'primary': '#7aa2f7',
        'secondary': '#bb9af7',
        'accent': '#f7768e'
    }
    
    plt.rcParams.update({
        'axes.facecolor': custom_colors['background'],
        'figure.facecolor': custom_colors['background'],
        'axes.labelcolor': custom_colors['text'],
        'xtick.color': custom_colors['text'],
        'ytick.color': custom_colors['text'],
        'text.color': custom_colors['text'],
        'grid.color': custom_colors['grid'],
        'font.size': 11,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'font.family': fuente_principal,
        'axes.unicode_minus': False
    })
    
    return custom_colors


def configurar_graficos():
    # Obtener la fuente apropiada
    fuente_principal = configurar_fuentes()
    
    plt.style.use("dark_background")
    custom_colors = {
        'background': '#1a1b26',
        'text': '#c0caf5',
        'grid': '#292e42',
        'primary': '#7aa2f7',
        'secondary': '#bb9af7',
        'accent': '#f7768e'
    }
    
    plt.rcParams.update({
        'axes.facecolor': custom_colors['background'],
        'figure.facecolor': custom_colors['background'],
        'axes.labelcolor': custom_colors['text'],
        'xtick.color': custom_colors['text'],
        'ytick.color': custom_colors['text'],
        'text.color': custom_colors['text'],
        'grid.color': custom_colors['grid'],
        'font.size': 11,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'font.family': fuente_principal,
        'axes.unicode_minus': False  # Ayuda con algunos problemas de renderizado
    })
    
    return custom_colors

def recortar_texto(texto, max_chars=30):
    """
    Recorta y sanitiza el texto
    """
    # Primero sanitizamos el texto
    texto_limpio = sanitizar_texto(texto)
    
    if len(texto_limpio) <= max_chars:
        return texto_limpio
    
    return texto_limpio[:max_chars] + "..."

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
    
    try:
        plt.savefig(path, 
                    dpi=150, 
                    bbox_inches='tight',
                    pad_inches=0.2,
                    facecolor=plt.rcParams['figure.facecolor'],
                    edgecolor='none')
        print(f"Gráfico guardado: {path}")
    except Exception as e:
        print(f"Error al guardar el gráfico: {e}")
        # Intentar guardar con configuración mínima en caso de error
        plt.savefig(path, dpi=150)


def plot_distribución_escuchas_artistas(df, carpeta, colors, usuarios_por_grafico=15):
    """
    Crea múltiples gráficos de distribución de artistas, divididos en grupos
    """
    # Contar artistas por usuario
    artistas_por_usuario = df.groupby('Usuario')['Artista'].count().sort_values()
    
    # Calcular número de gráficos necesarios
    total_usuarios = len(artistas_por_usuario)
    num_graficos = (total_usuarios + usuarios_por_grafico - 1) // usuarios_por_grafico
    
    for i in range(num_graficos):
        inicio = i * usuarios_por_grafico
        fin = min((i + 1) * usuarios_por_grafico, total_usuarios)
        
        # Obtener subset de datos
        usuarios_subset = artistas_por_usuario.iloc[inicio:fin]
        
        plt.figure(figsize=(14, 8))
        
        # Crear gradiente de colores
        gradient = np.linspace(0, 1, len(usuarios_subset))
        custom_cmap = LinearSegmentedColormap.from_list('custom', 
            [colors['primary'], colors['secondary'], colors['accent']])
        
        # Crear barras
        bars = plt.barh(range(len(usuarios_subset)), usuarios_subset.values,
                       color=custom_cmap(gradient))
        
        # Añadir valores en las barras
        for j, (value, name) in enumerate(zip(usuarios_subset.values, usuarios_subset.index)):
            plt.text(value + 1, j, f'{sanitizar_texto(name)} ({value})', 
                    va='center', color=colors['text'], fontsize=10)
        
        plt.yticks([])
        plt.xlabel('Número de artistas diferentes', fontsize=12, pad=15)
        plt.title(f'Distribución de artistas por usuario (Grupo {i+1} de {num_graficos})', 
                 fontsize=14, pad=20)
        
        plt.grid(axis='x', alpha=0.2)
        plt.tight_layout()
        
        guardar_grafico(f"distribucion_artistas_usuario_grupo_{i+1}.png", carpeta)
        plt.close()




def plot_artistas_populares(df, carpeta, colors, artistas_por_grafico=15):
    """
    Crea múltiples gráficos de artistas populares, divididos en grupos
    """
    # Contar frecuencia de artistas
    artistas_count = df['Artista'].value_counts()
    
    # Calcular número de gráficos necesarios
    total_artistas = len(artistas_count)
    num_graficos = (total_artistas + artistas_por_grafico - 1) // artistas_por_grafico
    
    for i in range(num_graficos):
        inicio = i * artistas_por_grafico
        fin = min((i + 1) * artistas_por_grafico, total_artistas)
        
        # Obtener subset de datos
        artistas_subset = artistas_count.iloc[inicio:fin]
        
        plt.figure(figsize=(14, 10))
        
        # Crear gradiente de colores para este subset
        colors_gradient = plt.cm.viridis(np.linspace(0, 1, len(artistas_subset)))
        
        # Crear barras horizontales
        artistas_nombres = [sanitizar_texto(x) for x in artistas_subset.index]
        bars = plt.barh(range(len(artistas_nombres)), 
                       artistas_subset.values,
                       color=colors_gradient)
        
        # Añadir etiquetas
        plt.yticks(range(len(artistas_nombres)), artistas_nombres)
        
        # Añadir valores en las barras
        for j, v in enumerate(artistas_subset.values):
            plt.text(v + 0.1, j, str(v), va='center', color=colors['text'])
        
        plt.xlabel("Número de usuarios", fontsize=12, labelpad=15)
        plt.ylabel("Artista", fontsize=12, labelpad=15)
        plt.title(f"Artistas más escuchados (Grupo {i+1} de {num_graficos})", fontsize=14, pad=20)
        plt.grid(axis='x', linestyle='--', alpha=0.2)
        
        plt.gca().invert_yaxis()
        plt.tight_layout()
        
        # Guardar con nombre único para cada grupo
        guardar_grafico(f"artistas_populares_grupo_{i+1}.png", carpeta)
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

def plot_usuarios_artistas_heatmap(df, carpeta, colors, max_usuarios_por_heatmap=15):
    """
    Crea múltiples heatmaps si hay demasiados usuarios
    """
    # Obtener lista única de usuarios
    usuarios = df['Usuario'].unique()
    
    # Calcular número de heatmaps necesarios
    total_usuarios = len(usuarios)
    num_heatmaps = (total_usuarios + max_usuarios_por_heatmap - 1) // max_usuarios_por_heatmap
    
    for i in range(num_heatmaps):
        inicio = i * max_usuarios_por_heatmap
        fin = min((i + 1) * max_usuarios_por_heatmap, total_usuarios)
        
        # Obtener subset de usuarios
        usuarios_subset = usuarios[inicio:fin]
        
        # Filtrar DataFrame para estos usuarios
        df_subset = df[df['Usuario'].isin(usuarios_subset)]
        
        plt.figure(figsize=(14, 10))
        
        # Crear matriz de coincidencias
        pivot = pd.crosstab(df_subset['Usuario'], df_subset['Artista'])
        
        # Calcular coincidencias y normalizar
        coincidencias = np.zeros((len(usuarios_subset), len(usuarios_subset)))
        for j in range(len(usuarios_subset)):
            for k in range(len(usuarios_subset)):
                artistas_comunes = (pivot.iloc[j] & pivot.iloc[k]).sum()
                total_artistas = (pivot.iloc[j] | pivot.iloc[k]).sum()
                coincidencias[j,k] = artistas_comunes / total_artistas if total_artistas > 0 else 0
        
        # Crear heatmap
        sns.heatmap(coincidencias, 
                    cmap='YlGnBu',
                    annot=True, 
                    fmt='.2f',
                    cbar_kws={'label': 'Índice de similitud'},
                    xticklabels=[sanitizar_texto(u) for u in usuarios_subset],
                    yticklabels=[sanitizar_texto(u) for u in usuarios_subset])
        
        plt.title(f"Similitud de gustos musicales entre usuarios (Grupo {i+1} de {num_heatmaps})", 
                 fontsize=14, pad=20)
        
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        plt.tight_layout()
        guardar_grafico(f"usuarios_coincidencias_grupo_{i+1}.png", carpeta)
        plt.close()

def procesar_datos(artists_data, carpeta):
    if not artists_data:
        print("No hay datos de artistas para procesar.")
        return
    
    # Crear DataFrame
    df = pd.DataFrame(artists_data, columns=["Usuario", "Artista"])
    
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    
    # Configurar estilo global
    custom_colors = configurar_graficos()
    
    # Generar gráficos divididos
    plot_artistas_populares(df, carpeta, custom_colors, artistas_por_grafico=15)
    plot_distribución_escuchas_artistas(df, carpeta, custom_colors, usuarios_por_grafico=15)
    plot_usuarios_artistas_heatmap(df, carpeta, custom_colors, max_usuarios_por_heatmap=15)
    
    # Guardar datos en JSON
    guardar_json(artists_data, os.path.join(carpeta, "artists_data.json"))
    
    generar_markdown_imagenes(carpeta, destino_md)
    
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
    rcParams['font.family'] = 'Firacode' # o la fuente que prefieras
    archivo_md = sys.argv[1]
    carpeta = sys.argv[2]
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
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
    # Después de crear tu DataFrame
    procesar_visualizaciones(
        df_canciones,
        carpeta_salida=f"{carpeta}/bonitas",
        archivo_md_salida=destino_md
    )