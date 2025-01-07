#!/usr/bin/env bash
#
# Script Name: get-links.sh
# Description: Obtener links de varias webs para un nuevo post.
# Author: volteret4
# Repository: https://github.com/volteret4/
# License:
# TODO:
# Notes:
#   Dependencies:   - python3 con los paquetes: lxml, google-api-python-client, requests, bs4
#                   - hugo, jq, git,
#                   - api accounts for: youtube, spotify, lastfm, discogs
#
#



# DECLARACION DE VARIABLES:

# Rutas.
enlaces_dir="${HOME}/hugo/hugo_scripts/blog/vvmm/post/enlaces"
post_dir="${HOME}/hugo/hugo_scripts/blog/vvmm/post"
blog="${HOME}/hugo/web/vvmm"

source "${HOME}/scripts/python_venv/bin/activate"

# Definir colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RESET='\033[0m'  # Restablece al color por defecto

# Parametros
artista="${1}"
albuma="${2}"
# eliminamos caracteres no alfanumericos.....que pena no poder poner una tilde
artist="$(bash "$HOME/hugo/hugo_scripts//limpiar_var.sh" "${artista}")"
album="$(bash $HOME/hugo/hugo_scripts//limpiar_var.sh ${albuma})"

# .env_root: COLORES!
#source ${HOME}/scripts/.env_root

# Generos o Estilos
tagA="${3}"
tagB="${4}"
tagC="${5}"
tagD="${6}"
tagE="${7}"


    # Actualizar playlists de spotify.

echo -e "${YELLOW}Actualizando listado de playlists y about_file.${RESET}"

about_file="$HOME/hugo/web/vvmm/content/about.md"

python3 $HOME/hugo/hugo_scripts//playlists/spotify/sp_playlist.py
python3 $enlaces_dir/spotify/sp_playlist_md.py
rm "${about_file}"
cp "${about_file}.skel" "${about_file}"
echo "" >> $about_file
echo "_Actualizado el "$(date +%d-%m-%Y)"_" >> $about_file
echo "" >> $about_file
cat $HOME/hugo/hugo_scripts//playlists/spotify/playlists.md >> $about_file

# echo "# Genero"
# echo "" >> $about_file
# cat $HOME/hugo/hugo_scripts//playlists/spotify/playlists_genre.md >> $about_file
# echo "" >> $about_file
# echo "# Humor"
# echo "" >> $about_file
# cat $HOME/hugo/hugo_scripts//playlists/spotify/playlists_mood.md >> $about_file
# echo "" >> $about_file
# echo "# Gentuza"
# echo "" >> $about_file
# cat $HOME/hugo/hugo_scripts//playlists/spotify/playlists_people.md >> $about_file
# echo "" >> $about_file



    # OBTENER ENLACES A SERVICIOS:

printf "\n%b%s%b\n" "${YELLOW}" "Obteniendo enlaces de webs de musica para el post..." "${RESET}"
echo -e "${GREEN}Ejecutando Scripts para:${RESET}"

# echo allmusic
#allmusic="$(python3 ${enlaces_dir}/allmusic.py ${artist} ${album})"

echo bandcamp
url_bandcamp="$(python3 ${enlaces_dir}/bandcamp/bandcamp.py "$artist" "$album" | sed 's/\?from=.*//')"

echo lastfm
url_lastfm="$(bash ${enlaces_dir}/lastfm/lastfm.sh "$artist" "$album")"


echo musicbrainz
url_musicbrainz="$(python3 ${enlaces_dir}/musicbrainz/musicbrainz.py "$artist" "$album")"

#echo rym
#url_rym="$(python3 ${enlaces_dir}/rym/rym.py ${artist} ${album})"

echo spotify
url_spotify="$(python3 ${enlaces_dir}/spotify/spotify.py "$artist" "$album")"

echo youtube
url_youtube="$(python3 ${enlaces_dir}/youtube/youtube.py "$artist" "$album")"

echo wikipedia
url_wikipedia="$(python3 ${enlaces_dir}/wikipedia/wikipedia.py "$artist" "$album" | tr -d '\n' | tr -d '\r')"

echo discogs
if [[ -f ${blog}/releases.txt ]] ; then rm "${blog}"/releases.txt ; fi           # elimina los releases del último post.
touch "${blog}"/releases.txt
masterid="$(python3 ${enlaces_dir}/discogs/discogs.py "$artist" "$album")"                  # master id de discogs para obtener info.

echo -e "${GREEN}Comprobando si existe master en discogs.${RESET}"

# lanzar script de bash para buscar releases si no hay masterid.
if [ $masterid = 'bash_script' ]
    then
        releaseid="$(python3 "${enlaces_dir}"/discogs/release_id.py "$album")"
        #url_discogs="$(echo "$temp_dg" | awk -F '_' '{print $2}')"
        #releaseid="$(echo "$temp_dg" | awk -F '_' '{print $1}')"
        echo "ES RELEASE ID: $releaseid"
        if [[ -z $releaseid ]]; then echo "No hay release id tampoco" ; exit 0 ; fi
    else
        if [[ $masterid =~ 'Error' ]]; then
            masterid="$(echo $masterid | sed 's/Error.*//')"
        fi
        url_discogs="https://www.discogs.com/master/$masterid"
        echo "ES MASTERID: $masterid"
fi

    
    # PREPARA EL POST:

# Rellena las variables con rutas de imagen y links. Si no existe, añade comentario para editarlo manualmente.
echo -e "${GREEN} Enlaces conseguidos:${RESET}"

# bandcamp
if [[ -z $url_bandcamp ]]; then 
    bandcamp="<!-- [![bandcamp](../links/svg/bandcamp.png (bandcamp))]("$url_bandcamp") url vacia -->"
elif [[ $url_bandcamp =~ 'error' ]]; then 
    bandcamp="<!-- [![bandcamp](../links/svg/bandcamp.png (bandcamp))]("$url_bandcamp") error busqueda -->"
else 
    bandcamp="[![bandcamp](../links/svg/bandcamp.png (bandcamp))]("https://bandcamp.com/search?q=$artista%20$album")"
    echo bandcamp
fi

# discogs
if [[ -z $url_discogs ]]; then 
    discogs="<!-- [![discogs](../links/svg/discogs.png (discogs))]("$url_discogs") -->"
else 
    discogs="[![discogs](../links/svg/discogs.png (discogs))]("$url_discogs")"
    echo discogs
fi

#lastfm
if [[ -z $url_lastfm ]]; then 
    lastfm="<!-- [![lastfm](../links/svg/lastfm.png (lastfm))]("$url_lastfm") -->"
elif [[ $url_lastfm =~ 'Por favor, proporciona un nombre de artista y álbum' ]]; then
    lastfm="<!-- [![lastfm](../links/svg/lastfm.png (lastfm))]("$url_lastfm") faltan argumentos -->"
elif [[ $url_lastfm =~ 'Error con la api de Lastfm' ]]; then
    lastfm="<!-- [![lastfm](../links/svg/lastfm.png (lastfm))]("$url_lastfm") error api key -->"
else 
    lastfm="[![lastfm](../links/svg/lastfm.png (lastfm))]("$url_lastfm")"
    echo lastfm
fi

# musicbrainz
if [[ -z $url_musicbrainz ]]; then 
    musicbrainz="<!-- [![musicbrainz](../links/svg/musicbrainz.png (musicbrainz))]("$url_musicbrainz") -->"
else 
    musicbrainz="[![musicbrainz](../links/svg/musicbrainz.png (musicbrainz))]("$url_musicbrainz")"
    echo musicbrainz
fi

# spotify
if [[ -z $url_spotify ]]; then 
    spotify="<!-- [![spotify](../links/svg/spotify.png (putify))]("$url_spotify") -->"
elif [[ $url_spotify =~ "Error" ]]; then
    echo "error en el script de spotify en\
        /home/pi/hugo/hugo_scripts//blog/vvmm/post/enlaces/spotify/spotify.py"
    exit 0
else 
    spotify="[![spotify](../links/svg/spotify.png (putify))]("$url_spotify")"
    echo spotify
fi

# wikipedia
if [[ -z $url_wikipedia ]]; then 
    wikipedia="<!-- [![wikipedia](../links/svg/wikipedia.png (wikipedia))]("$url_wikipedia") -->"
elif [[ $url_wikipedia =~ "error" ]]; then
    wikipedia="<!-- [![wikipedia](../links/svg/wikipedia.png (wikipedia))]("$url_wikipedia") -->"
elif [[ $url_wikipedia != 'error' ]] || [[ $url_wikipedia != 'None' ]]; then
    wikipedia="[![wikipedia](../links/svg/wikipedia.png (wikipedia))]("$url_wikipedia")"
    echo wikipedia
fi


# youtube
if [[ -z $url_youtube ]]; then 
    youtube="<!-- [![youtube](../links/svg/youtube.png (youtube))]("$url_youtube") -->"
else 
    youtube="[![youtube](../links/svg/youtube.png (youtube))]("$url_youtube")"
    echo youtube
fi




# TODO
#rym="[![rateyourmusic](../links/svg/sonemic.png (las leyendas cuentan que un dia tuvo el nombre de Sonemic))]("$url_rym")"



# CREA EL POST
printf "\n%b%s%b\n" "${YELLOW}" "Creando el post" "${RESET}"
cd ${blog}
post="${artist}-${album}"
artista_guion="${artist} _"                                         # Aqui adjunta el guion bajo
post_pre="${artista_guion}-${album}"
post_guiones="$(echo "$post_pre" | sed 's/ /-/g' | sed 's/,//g')"
post_file="${blog}/content/posts/${post_guiones}/index.md"
if [[ -f $post_file ]]
then
  echo "Ya existe el post $post_file"
  exit 1
else
    hugo new --kind post-bundle posts/${post_guiones}              # Aqui lo crea, con un guin bajo para que lo pase a normal en la web.
fi



    # ANADIR CONTENIDO AL POST


printf "\n%b%s%b\n" "$GREEN" "Añadiendo portada y enlaces..." "$RESET"

# Anadir iconos con urls al post.
echo "![cover](image.jpeg ($artist - $album))" >> "$post_file"
echo " " >> "$post_file"

# Almacenar las variables en un array
enlaces=("$bandcamp" "$discogs" "$lastfm" "$musicbrainz" "$spotify" "$wikipedia" "$youtube")

# Arrays para almacenar variables que cumplen con el criterio
non_comment_vars=()
comment_vars=()

# Clasificar las variables
for var in "${enlaces[@]}"; do
    if [[ $var == "<!-- "* ]]; then
        comment_vars+=("$var")
    else
        non_comment_vars+=("$var")
    fi
done

# Imprimir las variables que no empiezan con "<!-- "
#echo "Variables que no empiezan con '<!-- ':"
for var in "${non_comment_vars[@]}"; do
    echo "$var" >> "$post_file"
done
echo " " >> "$post_file"

# Imprimir las variables que empiezan con "<!-- "
#echo -e "\nVariables que empiezan con '<!-- ':"
for var in "${comment_vars[@]}"; do
    echo "$var" >> "$post_file"
done

# #echo "${allmusic}" >> "$post_file"
# echo "${bandcamp}" >> "$post_file"
# echo "${discogs}" >> "$post_file"
# echo "${lastfm}" >> "$post_file"
# echo "${musicbrainz}" >> "$post_file"
# #echo "${rym}" >> "$post_file"
# echo "${spotify}" >> "$post_file"
# echo "${youtube}" >> "$post_file"
# #echo "${wikipedia}" >> "$post_file"
echo " " >> "$post_file"


# Anadir CONTENIDO desde discogs.

printf "\n%b%s%b\n" "$GREEN" "Añadiendo info desde discogs..." "$RESET"
# Obtener info de discogs con masterid o releaseid.
if [[ $masterid != 'bash_script' ]]
    then
        echo "info desde el master id"
        python3 "${enlaces_dir}"/discogs/info_discogs.py "${masterid}" "$post_file"
        python3 "${enlaces_dir}"/discogs/info_release_discogs_extraartists.py "$masterid"
    elif [[ -n $releaseid ]]
        then
            echo "info desde el release id"
            python3 "${enlaces_dir}"/discogs/info_release_discogs.py "$releaseid" "$post_file"
            # Añadir info extra justo antes de tracklist
            python3 "${enlaces_dir}"/discogs/info_release_discogs_extraartists.py "$releaseid"
fi



# Divide el archivo original
csplit -f tracklist_parts --suppress-matched "${post_file}" '/Tracklist/'

# Copia de seguridad del post.
mv "$post_file" "${post_file}.BAK"

# Adjunta la primera parte.
mv tracklist_parts00 $post_file

# Mas info 
cat "${post_dir}/discogs_info_extra.txt" >> $post_file

# Aniade lineas.
echo '**Tracklist:**' >> $post_file
echo "" >> $post_file

# Incorpora seunda parte.
cat "tracklist_parts01" >> $post_file



rm tracklist_parts01
#rm $file_extra


    # CARÁTULA

printf "\n%b%s%b\n" "$GREEN" "Descargando carátulas" "$RESET"
# Descarga carátula de SPOTIFY.
post_folder="$(dirname $post_file)"
cd $post_folder
caratula="$(python3 "$post_dir"/portadas/caratula-spotify.py "$artist" "$album")"


# Descarga carátula de musicbrainz.
#caratula="$post_folder/image.jpeg" 
# if [[ $caratula != Error ]]; then
#     echo "caratula descargada desde spotify"
# else
#     bash $post_dir/portadas/portada_mb.sh "$artist" "$album" "$url_musicbrainz"
#     mv $HOME/hugo/web/vvmm/links/portada/image.jpeg $post_folder/image.jpeg
#     echo "caratula descargada desde music brainz"
# fi




# Descarga carátula de musicbrainz. _
#caratula="$post_folder/image.jpeg" 
if [[ $caratula =~ Error ]]; then
    python3  "$post_dir"/portadas/caratula-alternativa.py "$artist" "$album" "$post_folder"
    #bash $post_dir/portadas/portada_mb.sh "$artist" "$album" "$url_musicbrainz"
    #mv $HOME/hugo/web/vvmm/links/portada/image.jpeg $post_folder/image.jpeg
    echo "caratula descargada desde music brainz o discogs"
else
    echo "caratula descargada desde spotify"
fi





    # TAGS

# Aniade las TAGS si existieran.
printf "\n%b%s%b\n" "$GREEN" "Añade los tags..." "$RESET"
if [[ -n $tagA ]]
then
	sed -i 's/\#- tagA/- '"$tagA"'/' "${post_file}"
fi
if [[ -n $tagB ]]
    then
        sed -i 's/\#- tagB/- '"$tagB"'/' "${post_file}"
fi
if [[ -n $tagC ]]
    then
        sed -i 's/\#- tagC/- '"$tagC"'/' "${post_file}"
fi
if [[ -n $tagD ]]
    then
        sed -i 's/\#- tagD/- '"$tagD"'/' "${post_file}"
fi
if [[ -n $tagE ]]
    then
        sed -i 's/\tagE/- '"$tagE"'/' "${post_file}"
fi

if [[ -f "$HOME"/pollo.txt ]]; then
    pollo="$(cat $HOME/hugo/pollo.txt)"
    echo " " >> $post_file
    echo $pollo >> $post_file
    rm $HOME/hugo/pollo.txt
fi



    # COMENTAR CONTENIDO MARKDOWN
printf "\n%b%s%b\n" "${GREEN}" "Añadiendo formato comentado" "${RESET}"

# Nombre del archivo
file_name="$post_file"

# La línea desde donde empezar a añadir el símbolo
start_line="Información del álbum facilitada por discogs.com:"

# Archivo temporal para almacenar el resultado
temp_file=$(mktemp)

# Variable para indicar si hemos encontrado la línea de inicio
found_start_line=false

# Leer el archivo línea por línea
while IFS= read -r line
do
    # Comprobar si hemos encontrado la línea de inicio
    if $found_start_line; then
        echo "> $line" >> "$temp_file"
    else
        echo "$line" >> "$temp_file"
        if [[ "$line" == *"$start_line"* ]]; then
            found_start_line=true
        fi
    fi
done < "$file_name"

# Reemplazar el archivo original con el archivo temporal
mv "$temp_file" "$file_name"



    # Undraft.

sed -i 's/draft: true/draft: false/' "${post_file}"
echo "undraft"


    # Publicar con hugo.
printf "\n%b%s%b\n" "${YELLOW}" "Creando post..." "${RESET}"
cd ${blog}
hugo


# Subir a github.
printf "\n%b%s%b\n" "${GREEN}" "subiendo a github..." "${RESET}"
git add .
git commit -m "${artist} ${album}"
git push



#   DEBUG
echo ""
echo ""
echo ""
echo ""
echo "#############"
echo -e "## ${YELLOW} Contenido final del post.md ${RESET} ##"
echo "#############"
echo ""
echo ""
printf "%s\n" " " "CONTENIDO DEL INDEX.MD" " "
cat "${post_file}"

