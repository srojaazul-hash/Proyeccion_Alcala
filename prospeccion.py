import os
import requests
import pandas as pd
from dotenv import load_dotenv

# ==========================================================
# 1. CARGA SEGURA DE CREDENCIALES
# ==========================================================
# Esto lee el archivo .env y carga las variables
load_dotenv()

# Extraemos la clave de forma segura
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("¡Error! No se ha encontrado la GOOGLE_API_KEY en el archivo .env")

# ==========================================================
# 2. CONFIGURACIÓN DE BÚSQUEDA
# ==========================================================
LATITUD = 40.4819
LONGITUD = -3.3635
RADIO = 3000.0  

CATEGORIAS = ["car_repair", "hair_care", "restaurant"]

def buscar_negocios_sin_web(categoria):
    print(f"Buscando {categoria} en Alcalá...")
    url = "https://places.googleapis.com/v1/places:searchNearby"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.internationalPhoneNumber,places.websiteUri,places.formattedAddress"
    }

    payload = {
        "includedTypes": [categoria],
        "maxResultCount": 20, 
        "locationRestriction": {
            "circle": {
                "center": {"latitude": LATITUD, "longitude": LONGITUD},
                "radius": RADIO
            }
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        print(f"Error en {categoria}: {response.text}")
        return []

    lugares = response.json().get('places', [])
    leads = []

    for lugar in lugares:
        if 'websiteUri' not in lugar:
            leads.append({
                "Categoría": categoria,
                "Nombre": lugar.get('displayName', {}).get('text', 'Sin nombre'),
                "Teléfono": lugar.get('internationalPhoneNumber', 'No disponible'),
                "Dirección": lugar.get('formattedAddress', 'Sin dirección')
            })
    
    return leads

# ==========================================================
# 3. EJECUCIÓN PRINCIPAL
# ==========================================================
prospectos_totales = []

for cat in CATEGORIAS:
    leads_encontrados = buscar_negocios_sin_web(cat)
    prospectos_totales.extend(leads_encontrados)

# ==========================================================
# 4. EXPORTAR A EXCEL
# ==========================================================
if prospectos_totales:
    df = pd.DataFrame(prospectos_totales)
    nombre_archivo = "leads_alcala_sin_web.csv"
    df.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
    print(f"\n¡Éxito! Se han guardado {len(prospectos_totales)} negocios SIN WEB en '{nombre_archivo}'.")
else:
    print("\nNo se encontraron negocios sin web o hubo un error.")