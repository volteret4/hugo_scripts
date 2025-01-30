#!/usr/bin/env/bash

    # 1. Variabless

# Argumentos
mapfile -t archivos < <(find "$1" -type f -name "*.md")
tipo="$2"




# Rutas de scripts de Python
cancionpy="$HOME/hugo/hugo_scripts/blog/RYM/graficos/graficos_canciones.py"
albumpy="$HOME/hugo/hugo_scripts/blog/RYM/graficos/graficos_albumes.py"
artistapy="$HOME/hugo/hugo_scripts/blog/RYM/graficos/graficos_artistas.py"

# Ruta carpeta de gráficos
canciones="/home/pi/hugo/web/rym/static/graficos/${tipo}"
albumes="/home/pi/hugo/web/rym/static/graficos/${tipo}"
artistas="/home/pi/hugo/web/rym/static/graficos/${tipo}"

# Ruta de salida
salida_canciones="/home/pi/hugo/web/rym/content/estadisticas/${tipo}/"
salida_albumes="/home/pi/hugo/web/rym/content/estadisticas/${tipo}/"
salida_artistas="/home/pi/hugo/web/rym/content/estadisticas/${tipo}/"

# Ejecutar el script de Python según el tipo
# if [ "$tipo" == "semanal" ]; then
#     for file in "${archivos[@]}"; do
#         fecha=$(basename "$file" .md)
#         python3 "$cancionpy" "$file" "$canciones/$fecha/canciones" "$salida_canciones/$fecha/canciones/default.md"
#     done
#     exit 0
# elif [ "$tipo" == "mensual" ]; then
#     for file in "${archivos[@]}"; do
#         fecha=$(basename "$file" .md)
#         python3 "$albumpy" "$file" "$albumes/$fecha/albumes" "$salida_albumes/$fecha/albumes/default.md"
#     done
#     exit 0
# elif [ "$tipo" == "anual" ]; then
#     for file in "${archivos[@]}"; do
#         fecha=$(basename "$file" .md)
#         python3 "$artistapy" "$file" "$artistas/$fecha/artistas" "$salida_artistas/$fecha/artistas/default.md"
#     done
#     exit 0
# fi

# Ejecutar el script de Python para todos los archivos
for file in "${archivos[@]}"; do
        fecha=$(basename "$file" .md)
        python3 "$cancionpy" "$file" "$canciones/$fecha/canciones" "$salida_canciones/$fecha/canciones/default.md"
        python3 "$albumpy" "$file" "$albumes/$fecha/canciones" "$salida_albumes/$fecha/canciones/default.md"
        python3 "$artistapy" "$file" "$artistas/$fecha/canciones" "$salida_artistas/$fecha/canciones/default.md"
    done