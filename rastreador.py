import os
import requests
import pandas as pd
import math
import time
from dotenv import load_dotenv

# ==========================================================
# 1. PANEL DE CONTROL (MODIFICA ESTAS VARIABLES)
# ==========================================================
CATEGORIA = "hair_care"      # Negocio a buscar (ej: "hair_care", "car_repair")
RADIO_METROS = 800           # Radio de cada petición individual

# Coordenadas del centro geográfico de tu búsqueda
LATITUD_CENTRAL = 40.4850    # Coordenadas aproximadas del centro del área marcada
LONGITUD_CENTRAL = -3.3600

# Tamaño de la cuadrícula (Filas x Columnas)
FILAS_LATITUD = 2            # Eje vertical (Norte-Sur)
COLUMNAS_LONGITUD = 3        # Eje horizontal (Este-Oeste)
# Total de peticiones consumidas = FILAS * COLUMNAS (ej: 2x3 = 6 peticiones)

# ==========================================================
# 2. CARGA DE CREDENCIALES
# ==========================================================
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("¡Error! No se ha encontrado la GOOGLE_API_KEY en el archivo .env")

# ==========================================================
# 3. GENERADOR MATEMÁTICO DE CUADRÍCULA
# ==========================================================
def generar_coordenadas(lat_centro, lon_centro, radio, filas, columnas):
    coordenadas = []
    # El salto óptimo para solapar círculos y no dejar huecos es Radio * 1.5
    distancia_salto_metros = radio * 1.5
    
    # Conversión de metros a grados (aproximación terrestre estándar)
    # 1 grado de latitud = 111.32 km
    salto_lat_grados = distancia_salto_metros / 111320.0
    # 1 grado de longitud = 111.32 km * cos(latitud)
    salto_lon_grados = distancia_salto_metros / (111320.0 * math.cos(math.radians(lat_centro)))

    # Calcular los puntos (centrando la cuadrícula en las coordenadas base)
    for i in range(filas):
        offset_lat = i - (filas - 1) / 2.0
        lat_actual = lat_centro + (offset_lat * salto_lat_grados)
        
        for j in range(columnas):
            offset_lon = j - (columnas - 1) / 2.0
            lon_actual = lon_centro + (offset_lon * salto_lon_grados)
            
            coordenadas.append((lat_actual, lon_actual))
            
    return coordenadas

# ==========================================================
# 4. MOTOR DE BÚSQUEDA A LA API
# ==========================================================
def buscar_negocios(lat, lon, categoria, radio):
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
                "center": {"latitude": lat, "longitude": lon},
                "radius": radio
            }
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        print(f"Error en la API: {response.text}")
        return []

    lugares = response.json().get('places', [])
    leads = []

    for lugar in lugares:
        # Extraemos solo los que NO tienen página web (websiteUri)
        if 'websiteUri' not in lugar:
            leads.append({
                "Categoría": categoria,
                "Nombre": lugar.get('displayName', {}).get('text', 'Sin nombre'),
                "Teléfono": lugar.get('internationalPhoneNumber', 'No disponible'),
                "Dirección": lugar.get('formattedAddress', 'Sin dirección')
            })
    
    return leads

# ==========================================================
# 5. EJECUCIÓN DEL BARRIDO (GRID SEARCH)
# ==========================================================
print(f"Iniciando barrido de '{CATEGORIA}'...")
print(f"Generando cuadrícula de {FILAS_LATITUD}x{COLUMNAS_LONGITUD} ({FILAS_LATITUD * COLUMNAS_LONGITUD} peticiones)...")

lista_puntos = generar_coordenadas(LATITUD_CENTRAL, LONGITUD_CENTRAL, RADIO_METROS, FILAS_LATITUD, COLUMNAS_LONGITUD)
prospectos_totales = []

for idx, (lat, lon) in enumerate(lista_puntos):
    print(f"Petición {idx + 1}/{len(lista_puntos)} -> Buscando en Lat: {lat:.5f}, Lon: {lon:.5f}")
    leads_encontrados = buscar_negocios(lat, lon, CATEGORIA, RADIO_METROS)
    prospectos_totales.extend(leads_encontrados)
    
    # Pausa de seguridad de 1 segundo para no saturar los servidores de Google
    time.sleep(1)

# ==========================================================
# 6. FILTRADO FINAL Y EXPORTACIÓN
# ==========================================================
if prospectos_totales:
    df = pd.DataFrame(prospectos_totales)
    
    # Al solaparse los círculos, habrá negocios repetidos. Los eliminamos aquí:
    total_bruto = len(df)
    df = df.drop_duplicates(subset=['Nombre', 'Dirección'])
    total_limpio = len(df)
    
    nombre_archivo = f"leads_{CATEGORIA}_grid.csv"
    df.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
    
    print("\n--- RESULTADOS DEL BARRIDO ---")
    print(f"Leads brutos extraídos: {total_bruto}")
    print(f"Duplicados eliminados: {total_bruto - total_limpio}")
    print(f"Leads únicos guardados: {total_limpio}")
    print(f"Archivo generado: {nombre_archivo}")
else:
    print("\nEl barrido ha finalizado, pero no se encontraron negocios sin web en la zona.")