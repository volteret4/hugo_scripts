#!/usr/bin/env bash
#
# Script Name: git.sh
# Description: Atajo para subir hacer git push con todo, solicitando nombre del commit interactivamente.
# Author: volteret4
# Repository: https://github.com/volteret4/
# License:
# TODO:
# Notes:
#   Dependencies:   - git
#

# Pedir al usuario el mensaje del commit
echo "Introduce el mensaje del commit:"
read commit_message

# Añadir todos los archivos al área de preparación
git add .

# Realizar el commit con el mensaje proporcionado por el usuario
git commit -m "$commit_message"

# Subir los cambios al repositorio remoto
git push
