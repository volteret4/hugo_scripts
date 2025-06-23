#!/bin/bash

# Directorio donde tienes los archivos Markdown creados en Obsidian para los posts
POSTS_DIR="/mnt/NFS/blogs/tumtumpa"

# Directorio de tu repositorio Hugo
HUGO_DIR="/home/pepe/hugo/web/tumtumpa"

# Seleccionar un archivo Markdown aleatorio de la carpeta de posts
OBSIDIAN_FILE=$(find $POSTS_DIR/*.md | shuf -n 1)

# Verificar que se haya seleccionado un archivo
if [ -z "$OBSIDIAN_FILE" ]; then
  echo "No se encontraron archivos Markdown en $POSTS_DIR"
  exit 1
fi


# Obtener variables
post_name="$(basename "$OBSIDIAN_FILE")"
echo "postn_name:$post_name"

artista="$(echo "$post_name" | awk -F'-' '{print $1}')"
artista="$(echo "$artista" | sed -E "s/[áÁ]/-/g; s/\(.*\)//g; s/&/and/g; s/[éÉ]/e/g; s/[íÍ]/i/g; s/[óÓ]/o/g; s/[úÚ]/u/g; s/['\`]/-/g; s/---/-/g; s/--/-/g; s/\ //g; s/^-//g; s/-$//g")"
echo "A $artista"

album="$(echo "$post_name" | awk -F'-' '{print $2}' | sed -E 's/\.md$//')"
album="$(echo "$album" | sed -E "s/[áÁ]/-/g; s/\(.*\)//g; s/\[.*\]//g; s/\{.*\}//g; s/&/and/g; s/[éÉ]/e/g; s/[íÍ]/i/g; s/[óÓ]/o/g; s/[úÚ]/u/g; s/['\`]/-/g; s/---/-/g; s/--/-/g; s/\ /-/g; s/^-//g; s/-$//g")"
echo "B $album"


# Establecer ruta a carpeta del post
titulo_post="$artista-_-$album"
echo "a-_-b: $titulo_post"


# Copiar el archivo al directorio de posts de Hugo
#mkdir "$HUGO_DIR/content/post/${titulo_post}"
HUGO_POST="$HUGO_DIR/content/posts/${titulo_post}/index.md"

# Crear el post con hugo
if [[ -f $HUGO_POST ]]
then
  echo "Ya existe el post $post_name"
  exit 1
else
  cd "${HUGO_DIR}" || exit && hugo new --kind post-bundle posts/"${titulo_post}"              # Aqui lo crea, con un guión bajo para que lo pase a normal en la web.
  cp "$OBSIDIAN_FILE" "$HUGO_POST"
fi

# Obtener tags
tags="$(grep tags "$HUGO_POST" | sed 's/tags: //')"
IFS=',' read -r tag1 tag2 tag3 tag4 tag5 <<< "$tags"
echo "C $tags"


# Añadir tags correctos para hugo
tags_hugo=$(cat <<EOF
tags:
  - $tag1
  - $tag2
  - $tag3
  - $tag4
  - $tag5
EOF
)

awk -v new_tags="$tags_hugo" '
    /^tags:/ { print new_tags; next }
    { print }
' "$HUGO_POST" > temp_file && mv temp_file "$HUGO_POST"

# Cambiar fecha a la actual
fecha="$(date +%Y-%m-%d)"
sed -i "s/^lastmod:.*/lastmod: $fecha/" "$OBSIDIAN_FILE"
sed -i "s/^lastmod:.*/lastmod: $fecha/" "$HUGO_POST"

# Eliminar borrador
sed -i "s/^draft\: true/draft\: false/" "$OBSIDIAN_FILE"
sed -i "s/^draft\: true/draft\: false/" "$HUGO_POST"



# Añadir a vvmm
bash /home/pepe/Scripts/hugo_scripts/blog/vvmm/post/get-links.sh "${artista}" "${album}" $tags


# Copiar imagen de vvmm
cp "${HOME}/hugo/web/vvmm/content/posts/${titulo_post}/image.jpeg" "$HUGO_DIR/content/posts/${titulo_post}/cover.jpg"


# Copiar links de vvmm.
vvmm_post="/home/pepe/hugo/web/vvmm/content/posts/$titulo_post/index.md"

bandcamp_url=$(awk '/bandcamp/ {print}' "$vvmm_post" | sed 's/.*(\(.*\))/\1/' | sed 's/ -->//')
wikipedia_url=$(awk '/wikipedia/ {print}' "$vvmm_post" | sed 's/.*(\(.*\))/\1/' | sed 's/ -->//')
discogs_url=$(awk '/https:\/\/www\.discogs/ {print}' "$vvmm_post" | sed 's/.*(\(.*\))/\1/' | sed 's/ -->//')
lastfm_url=$(awk '/lastfm/ {print}' "$vvmm_post" | sed 's/.*(\(.*\))/\1/' | sed 's/ -->//')
spotify_url=$(awk '/spotify/ {print}' "$vvmm_post" | sed 's/.*(\(.*\))/\1/' | sed 's/ -->//')
youtube_url=$(awk '/youtube/ {print}' "$vvmm_post" | sed 's/.*(\(.*\))/\1/' | sed 's/ -->//')
musicbrainz_url=$(awk '/musicbrainz/ {print}' "$vvmm_post" | sed 's/.*(\(.*\))/\1/' | sed 's/ -->//')

echo "lastfm $lastfm_url"

# Añadir links al post.
output=""

if [[ -n $discogs_url ]]; then
    output+="[discogs]($discogs_url) "
fi

if [[ -n $musicbrainz_url ]]; then
    output+="[musicbrainz]($musicbrainz_url) "
fi

if [[ -n $lastfm_url ]]; then
    output+="[lastfm]($lastfm_url) "
fi

if [[ -n $wikipedia_url ]]; then
    output+="[wikipedia]($wikipedia_url) "
fi

if [[ -n $bandcamp_url ]]; then
    output+="[bandcamp]($bandcamp_url) "
fi

if [[ -n $spotify_url ]]; then
    output+="[spotify]($spotify_url) "
fi

if [[ -n $youtube_url ]]; then
    output+="[youtube]($youtube_url)"
fi

echo "output: $output"

# Escribir la salida en el archivo si no está vacía
if [[ -n $output ]]; then
    #echo " " >> "$HUGO_POST"
    #echo "$output" >> "$HUGO_POST"
    #output_escaped="$(echo "$output" | sed 's/[&/\]/\\&/g')"
    #sed -E "s#linkkks#$output_escaped#" "$HUGO_POST"
  
    sed -i "s|linkkks|$output|" "$HUGO_POST"
fi


cat "$HUGO_POST"

#cd "${HUGO_DIR}" || exit ; git add . ; git commit -m "${post_name}"; git push

# Mover el post.
#mv "$OBSIDIAN_FILE" "$POSTS_DIR/publicado/"

# Mensaje de confirmación
echo "Post '$post_name' ha sido subido con éxito!"