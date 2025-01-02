import requests
import sys
from dotenv import load_dotenv
import os

master_id = sys.argv[1]

load_dotenv()
DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN")

def get_main_release_id(master_id):
    # Construye la URL para obtener información del master
    master_url = f"https://api.discogs.com/masters/{master_id}"
    
    # Realiza la solicitud para obtener la información del master
    response = requests.get(master_url)
    
    # Verifica si la respuesta fue exitosa
    if response.status_code!= 200:
        print(f"Error al buscar el master_id '{master_id}'. Código de estado: {response.status_code}")
        return None
    
    # Intenta procesar la respuesta como JSON
    try:
        data = response.json()
    except ValueError:
        print(f"Error al parsear la respuesta como JSON. Respuesta recibida: {response.text}")
        return None
    
    # Verifica si se encontraron resultados
    if 'status' in data and data['status'] == 'error':
        print(f"Error al buscar el master_id '{master_id}'.")
        return None
    
    # Si el master tiene un release principal, devuelve su ID
    if 'main_release' in data:
        main_release_id = data['main_release']['id']
        print(f"El ID del release principal es: {main_release_id}")
        return main_release_id
    
    print(f"No se encontró un release principal para el master_id '{master_id}'.")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 enlaces/discogs_release_from_masterid.py [master_id]")
        sys.exit(1)
    
    main_release_id = get_main_release_id(master_id)