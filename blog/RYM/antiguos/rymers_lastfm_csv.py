import gspread
import re

# ID de la hoja de cálculo
SPREADSHEET_ID = "1Oxtg_U6yOJ1zu3IjaML8jcC4Kw-aPypcEBbPhalrZ6I"  # Cambia esto por el ID real

# Autenticación anónima (para hojas públicas)
gc = gspread.public()

# Abre la hoja de cálculo y selecciona la primera hoja
sh = gc.open_by_key(SPREADSHEET_ID)
worksheet = sh.get_worksheet(0)  # Primera hoja

# Obtener todas las filas a partir de la segunda fila
data = worksheet.get_all_values()[1:]  # Omitimos la primera fila (títulos)

# Extraer la segunda columna (índice 1)
links = [row[1] for row in data if len(row) > 1]

# Función para extraer nombres de usuario desde URLs
def extract_username(url):
    match = re.search(r"/([^/]+)$", url)  # Captura la última parte de la URL
    return match.group(1) if match else None

# Obtener nombres de usuario
usernames = [extract_username(link) for link in links]

print(usernames)
