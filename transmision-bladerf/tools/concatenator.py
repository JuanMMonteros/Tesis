import os # Manejo de archivos
import re # Expresiones regulares

# ==============================
# Configuración
carpeta_origen = "./bin"                 # Carpeta donde están los archivos a concatenar
carpeta_destino = "./bin"                # Carpeta donde se guardará el archivo concatenado
archivo_inicial = "chirp_SC16_Q11_0.bin" # Nombre del primer archivo a concatenar (termina en _x.bin)
# ==============================

def concatenar_bins(carpeta_origen, carpeta_destino, archivo_inicial):
    # Construir la ruta completa del archivo inicial
    ruta_inicial = os.path.join(carpeta_origen, archivo_inicial)
    base, ext = os.path.splitext(ruta_inicial)

    # Buscar el patrón "_<número>" al final del nombre base
    match = re.match(r"^(.*)_(\d+)$", base)
    if not match:
        raise ValueError("El nombre debe terminar con _<número>, por ejemplo my_binario_0.bin")

    base_sin_indice = match.group(1)
    partes = []

    i = 0
    while True:
        nombre = f"{base_sin_indice}_{i}{ext}"
        if not os.path.exists(nombre):
            break
        partes.append(nombre)
        i += 1

    if not partes:
        raise FileNotFoundError(f"No se encontró ningún archivo que comience con {ruta_inicial}")

    # Verificar tamaños
    tamaños = [os.path.getsize(p) for p in partes]

    if len(set(tamaños)) != 1:
        raise ValueError(f"Error: Los archivos no tienen el mismo tamaño ({tamaños})")

    # Crear la carpeta de destino si no existe
    os.makedirs(carpeta_destino, exist_ok=True)

    # Concatenar
    salida = os.path.join(carpeta_destino, f"{os.path.basename(base_sin_indice)}_concat{ext}")
    with open(salida, "wb") as fout:
        for p in partes:
            with open(p, "rb") as fin:
                contenido = fin.read()
                print(f"Escribiendo {len(contenido)} bytes del archivo {p}")
                fout.write(contenido)

    print(f"{len(partes)} concatenaciones completadas. Archivo de salida: {salida}")
    return {len(partes)}


if __name__ == "__main__":
    try:
        concatenar_bins(carpeta_origen, carpeta_destino, archivo_inicial)
    except Exception as e:
        print(f"Error: {e}")
