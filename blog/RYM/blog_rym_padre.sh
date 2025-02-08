#! /usr/bin/env bash

# Variables principales
RYM_BLOG="$HOME/hugo/web/rym"
RYM_SCRIPTS="$HOME/hugo/hugo_scripts/blog/RYM"


# Initialize script run flags
monthly_script_ran=false
yearly_script_ran=false
weekly_script_ran=false


# Telegram Bot Configuration
source /home/pi/hugo/hugo_scripts/blog/RYM/.env

# Activate Python virtual environment
source "$HOME/scripts/python_venv/bin/activate"


# Function to send Telegram message
send_telegram_message() {
    local message="$1"
    local parse_mode="${2:-}"
    
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
         -d "chat_id=$TELEGRAM_CHAT_ID" \
         -d "text=$message" \
         ${parse_mode:+-d "parse_mode=$parse_mode"}
}

# Capture script output
exec > >(tee -a /tmp/rym_script_log.txt) 2>&1



# Weekly script execution

cd "$RYM_BLOG" || {
    send_telegram_message "❌ Failed to change directory to $blog_dir"
    exit 1
}

weekly_script() {
    fecha="$(date +"%d-%m-%y")"
    hugo new --kind posts semanal/$fecha.md
    semanal="$RYM_BLOG/content/semanal/$fecha.md"
    
    if [ -f "$RYM_BLOG/lastfm_weekly_stats.md" ]; then rm "$RYM_BLOG/lastfm_weekly_stats.md";fi
    
    python3 "$RYM_SCRIPTS/blog_rym.py" || {
        send_telegram_message "❌ Error in blog_rym.py. Check log at /tmp/rym_script_log.txt" "Markdown"
        return 1
    }
    
    echo "log semanal realizado $RYM/lastfm_weekly_stats.md"
#    echo '<!--more-->' >> "$semanal"
    echo "" >> "$semanal"
    sed "s/title/title \= $fecha/" "$semanal"
    cat "$RYM_BLOG/lastfm_weekly_stats.md" >> "$semanal"
    echo "post creado en $semanal"
    send_telegram_message "✅ Weekly RYM script completed successfully for $fecha" "Markdown"
    weekly_script_ran=true
}


# Monthly script execution #TODO
monthly_script() {
    hoy=$(date +%d)
    dia_semana="$(date +%A)"
    mes="$(date +%B-%y)"
    post="$RYM_BLOG/content/mensual/$mes.md"
    
    if [ "$hoy" == "01" ];then
        echo "iniciando log mensual $mes"
        cd "$blog_dir" || { echo "Error al cambiar de directorio"; exit 1; }
        hugo new --kind posts mensual/$mes.md
        python3 "$RYM_SCRIPTS/blog_rym_mensual.py"
        #sed 's/tipo/mensual: true/' "$RYM_BLOG/content/mensual/$mes.md"
        echo "" >> "$post"
        cat "$RYM_BLOG/lastfm_monthly_stats.md" >> "$post"
        monthly_script_ran=true
    fi
}

# Yearly script execution #TODO
yearly_script() {
    hoy="$(date +%m-%d)"
    anio="$(date +%Y)"
    if [ "$hoy" == "01-01" ]; then
        echo "iniciando log mensual $anio"
        cd "$blog_dir" || { echo "Error al cambiar de directorio"; exit 1; }
        hugo new --kind posts anual/$anio.md
        #sed 's/tipo/anual: true/' "$RYM_BLOG/content/anual/$anio.md"
        python3 "$RYM_SCRIPTS/blog_rym_anual.py"
        cat "$RYM_BLOG/lastfm_yearly_stats.md" >> "$RYM_BLOG/content/anual/$anio.md"
        yearly_script_ran=true
    fi
}


# Función para generar gráficos
generar_graficos() {
    tipo=$1  # tipo de gráfico (canciones, albumes, artistas)
    periodo=$2  # periodo (semanal, mensual, etc.)
    archivo_md=$3  # destino del archivo Markdown donde se van a generar las gráficas

    # Establecer fecha segun el periodo
    if [ $periodo == "semanal" ]; then
        fecha="$(date +"%d-%m-%y")"
    elif [ $periodo == "mensual" ]; then
        fecha="$(date +"%B-%y")"
    elif [ $periodo == "anual" ]; then
        fecha="$(date +"%Y")"
    fi  

    
    # Definir script de gráficos y rutas
    script_graficos="$RYM_SCRIPTS/graficos/graficos_$tipo.py"
    graf_dir="$RYM_BLOG/static/graficos/$periodo/$fecha/$tipo"
    graf_post="$RYM_BLOG/content/estadisticas/$periodo/$fecha/default.md"

    # Crear o añadir contenido al archivo Markdown
    echo "" >> "$graf_post"
    echo "# Gráfico $periodo de $tipo" >> "$graf_post"
    echo "" >> "$graf_post"
    
    # Generar gráfico con el script correspondiente
    echo "Generando gráfico $periodo para $tipo..."
    python3 "$script_graficos" "$archivo_md" "$graf_dir" "$graf_post"
}

# Función para agregar imágenes a un archivo Markdown
agregar_imagenes_markdown() {
    directorio=$1  # directorio donde buscar los archivos
    graf_post_artist=$2  # archivo Markdown donde se agregará el contenido

    echo "# Gráfico $periodo de artistas" >> "$graf_post_artist"
    # Recorremos todos los archivos .png dentro del directorio y subdirectorios
    find "$directorio" -type f -name "*.png" | while read -r archivo; do
        # Extraemos el nombre del archivo sin la ruta
        nombre_archivo=$(basename "$archivo")
        # Extraemos el nombre de la carpeta que contiene el archivo
        carpeta=$(dirname "$archivo" | sed 's|.*/||')
        # Convertimos la ruta a formato Markdown y la agregamos al archivo .md
        echo "" >> "$graf_post_artist"  # Agrega un salto de línea adicional
        echo "" >> "$graf_post_artist"
        echo "![${nombre_archivo%.*}](/rym/graficos/semanal/$carpeta/$nombre_archivo)" >> "$graf_post_artist"
        echo "" >> "$graf_post_artist"  # Agrega un salto de línea adicional
    done
}



# Main execution block
if weekly_script; then
    monthly_script
    yearly_script

    # Send notifications for monthly and yearly scripts
    if $weekly_script_ran; then
        send_telegram_message "✅ Weekly script executed successfully" "Markdown"
        echo "Semanal exitoso.mensaje telegram enviado"
    else
        send_telegram_message "❌ Weekly script error" "Markdown"
        echo "Semanal fracasado. Telegram enviado"
    fi

    if $monthly_script_ran; then
        send_telegram_message "✅ Monthly script executed successfully" "Markdown"
        echo "MENSUAL exitoso.mensaje telegram enviado"
    fi

    if $yearly_script_ran; then
        send_telegram_message "✅ Yearly script executed successfully" "Markdown"
        echo "ANUAL exitoso.mensaje telegram enviado"
    fi
else
    send_telegram_message "❌ Weekly script failed. Stopping execution." "Markdown"
    echo "O no toca hoy, o algo va mal"
fi


    # Estadisticas GRÁFICAS post semanal

echo "Creando estadisticas graficas semanales"

if $weekly_script_ran; then
    fecha=$(date +"%d-%m-%y")
    periodo="semanal"
    # Markdown semanal a leer
    archivo_md="$RYM_BLOG/content/$periodo/$fecha.md"
    
    # crear carpeta para las graficas
    mkdir -p "$RYM_BLOG"/static/graficos/"$periodo"/"$fecha"/{canciones artistas albumes}

    # crear  post estadistica
    echo "creando post hugo"
    hugo new --kind post_bundle estadisticas/$periodo/$fecha
    

    # Llamada a la función para generar gráficos de canciones
    generar_graficos "canciones" "$periodo" "$archivo_md"

    # Llamada a la función para generar gráficos de álbumes
    generar_graficos "albumes" "$periodo" "$archivo_md"

    # Llamada a la función para generar gráficos de artistas
    generar_graficos "artistas" "$periodo" "$archivo_md"

    # Llamada a la función para agregar imágenes a Markdown (solo para artistas)
    agregar_imagenes_markdown "$RYM_BLOG/static/graficos/$periodo/$fecha/artistas" "$RYM_BLOG/content/estadisticas/$periodo/$fecha/default.md"
    #     # GENERAR GRAFICOS        POLLO_OG
       
    # # Generar graficos semanales por canciones
    # tipo=canciones
    # # Script
    # script_graficos="$RYM_SCRIPTS/graficos/graficos_$tipo.py"
    # # Rutas destino
    # graf_dir="$RYM_BLOG/static/graficos/$periodo/$fecha/$tipo"
    # graf_post="$RYM_BLOG/content/estadisticas/$periodo/$fecha/default.md"
    # echo "" >> "$graf_post"
    # echo "# Gráfico $periodo de $tipo"
    # echo "" >> "$graf_post"
    
    # echo "generando grafico $periodo $tipo"
    # python3 $script_graficos "$archivo_md" "$graf_dir" "$graf_post"


    # # Generar graficos estadisticas albums
    # tipo=albumes
    # # Script
    # script_graficos="$RYM_SCRIPTS/graficos/graficos_$tipo.py"
    # # Rutas destino
    # graf_dir="$RYM_BLOG/static/graficos/$periodo/$fecha/$tipo"
    # graf_post="$RYM_BLOG/content/estadisticas/$periodo/$fecha/default.md"

    # echo "generando grafico $periodo $tipo"
    # python3 "$script_graficos"  "$archivo_md" "$graf_dir" "$graf_post"


    # # Generar graficos estadisticas artistas
    # tipo=artistas
    # # Script
    # script_graficos="$RYM_SCRIPTS/graficos/graficos_$tipo.py"
    # # Rutas destino
    # graf_dir="$RYM_BLOG/static/graficos/$periodo/$fecha/$tipo"
    # graf_post="$RYM_BLOG/content/estadisticas/$periodo/$fecha/default.md"

    # echo "generando grafico $periodo $tipo"
    # python3 "$script_graficos" "$archivo_md" "$graf_dir" "$graf_post"
    

    # # Este python de los artistas no crea el markdown, asi que:
    # # Función para agregar imágenes a un archivo .md
    # agregar_imagenes_markdown() {
    #     # Directorio donde buscar los archivos
    #     directorio=$1
    #     # Archivo Markdown donde se agregará el contenido
    #     archivo_md=$2

    #     # Recorremos todos los archivos .png dentro del directorio y subdirectorios
    #     find "$directorio" -type f -name "*.png" | while read -r archivo; do
    #         # Extraemos el nombre del archivo sin la ruta
    #         nombre_archivo=$(basename "$archivo")
    #         # Extraemos el nombre de la carpeta que contiene el archivo, para crear el formato Markdown
    #         carpeta=$(dirname "$archivo" | sed 's|.*/||')
    #         # Convertimos la ruta a formato Markdown y la agregamos al archivo .md
    #         echo "" >> "$archivo_md"  # Agrega un salto de línea adicional
    #         echo "# Gráfico $periodo de $tipo"
    #         echo "" >> "$archivo_md"
    #         echo "![${nombre_archivo%.*}](/rym/graficos/semanal/$carpeta/$nombre_archivo)" >> "$graf_post"
    #         echo "" >> "$archivo_md"  # Agrega un salto de línea adicional
    #     done

    #     # Ejemplo de uso:
    #     # especifica el directorio y el archivo Markdown donde quieres agregar las imágenes
    #     directorio="$RYM_BLOG/static/graficos/semanal/$fecha/$tipo"

    # }
    # # Llamamos a la función
    # agregar_imagenes_markdown "$graf_dir" "$graf_post"
fi




# Estadisticas graficas post mensual

if $monthly_script_ran; then
    echo "Creando graficos mensual"
    periodo="mensual"
    fecha=$(date +"%m-%y")
    # crear carpeta para las graficas
    mkdir -p "$RYM_BLOG"/static/graficos/"$periodo"/"$fecha"/{canciones artistas albumes}
    # crear diferentes post estadistica
    hugo new --kind post_bundle estadisticas/$periodo/"${fecha}"
    
        # Llamada a la función para generar gráficos de canciones
    generar_graficos "canciones" "$periodo" "$archivo_md"

    # Llamada a la función para generar gráficos de álbumes
    generar_graficos "albumes" "$periodo" "$archivo_md"

    # Llamada a la función para generar gráficos de artistas
    generar_graficos "artistas" "$periodo" "$archivo_md"

    # Llamada a la función para agregar imágenes a Markdown (solo para artistas)
    agregar_imagenes_markdown "$RYM_BLOG/static/graficos/$periodo/$fecha/artistas" "$RYM_BLOG/content/estadisticas/$periodo/$fecha/default.md"
fi




# Estadisticas graficas post anual

if $yearly_script_ran; then
    echo "Creando graficos anuales"
    periodo="anual"
    fecha="$(date +%Y)"
    # crear carpeta para las graficas
    mkdir -p "$RYM_BLOG"/static/graficos/"$periodo"/"$fecha"/{canciones artistas albumes}
    # crear diferentes post estadistica
    hug new --kind post_bundle estadisticas/"${periodo}"/"${fecha}"
    

        # Llamada a la función para generar gráficos de canciones
    generar_graficos "canciones" "$periodo" "$archivo_md"

    # Llamada a la función para generar gráficos de álbumes
    generar_graficos "albumes" "$periodo" "$archivo_md"

    # Llamada a la función para generar gráficos de artistas
    generar_graficos "artistas" "$periodo" "$archivo_md"

    # Llamada a la función para agregar imágenes a Markdown (solo para artistas)
    agregar_imagenes_markdown "$RYM_BLOG/static/graficos/$periodo/$fecha/artistas" "$RYM_BLOG/content/estadisticas/$periodo/$fecha/default.md"
fi



    # Subir a github pages.

#cd "$blog_dir" || exit 0 ; git add . ; git commit -m "" ; git push