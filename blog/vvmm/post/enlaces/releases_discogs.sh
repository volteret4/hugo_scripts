#!/usr/bin/env bash
#
# Script Name: releases_discogs.sh
# Description: Obtener link de release album poasado como argumento.
# Author: volteret4
# Repository: https://github.com/volteret4/
# License:
# TODO: Añadir esta funcionalidad a discogs.py y eliminar este script.
# Notes:
#   Dependencies: Este script solo funciona como "hijo"  de discogs.py, para continuar el trabajo sucio..
#

# Verificar que se proporcionó un álbum como argumento
if [[ $# -ne 1 ]]; then
    echo "Uso: $0 'Nombre del Álbum'"
    exit 1
fi

album="$1"
file="$HOME/hugo/web/vvmm/releases.txt"

# Salir si no existe el archivo releases.txt
if [[ ! -e $file ]]; then
    echo "Error: No se encontró el archivo releases.txt"
    exit 1
fi

# Función para normalizar caracteres
normalize_line() {
    local line="$1"
    # Sustituir caracteres acentuados por caracteres sin acento
    line=$(echo "$line" | sed -e 's/á/a/g' -e 's/é/e/g' -e 's/í/i/g' -e 's/ó/o/g' -e 's/ú/u/g' \
                               -e 's/Á/A/g' -e 's/É/E/g' -e 's/Í/I/g' -e 's/Ó/O/g' -e 's/Ú/U/g')
    echo "$line"
}

# Leer cada línea del archivo
while IFS= read -r line || [[ -n "$line" ]]; do
    # Normalizar la línea
    normalized_line=$(normalize_line "$line")
    echo "$normalized_line"
done < "$file"


# Leer el archivo sin modificarlo y buscar el álbum deseado
line=$(grep -i "$album" "$file")

# Verificar si se encontró el álbum
if [[ -z "$line" ]]; then
        exit 1
fi

# Obtener la URL del release
url=$(echo "$line" | awk -F ' - ' '{print $NF}')

# Obtener el release ID desde la URL
releaseid=$(echo "$url" | awk -F '/' '{print $NF}')

# Obtener el URL del álbum utilizando curl y jq
album_url=$(curl -s "$url" | jq -r '.uri')

# Imprimir la información
echo "URL del álbum '$album': $album_url"
echo "ID del release: $releaseid"