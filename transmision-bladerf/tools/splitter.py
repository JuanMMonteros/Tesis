import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import os
import re
import shutil

# ==============================
# Configuración       
START_INDEX = 1000 
END_INDEX   = 2000 # -1 para procesar hasta el final
inFileI = "radar_capture/W616T48104495_canal_vv_I.bin"  # Archivo I a procesar
inFileQ = "radar_capture/W616T48104495_canal_vh_Q.bin"  # Archivo Q a procesar

fmt = 'SC16_Q11'    # Cambiar a 'SC8_Q7' o 'SC16_Q11'
fs  = 38e6          # Frecuencia de muestreo
nElementsCount = 4096  # cantidad de muestras por archivo a dividir
OFFSET = 6.0        # valor de offset a restar a las muestras

plot_en = False
samplesToGraphic = 3800000  # cantidad de muestras a graficar

carpeta_origen = "./bin/split_files"
DELETE_SPLIT_FILES = True
carpeta_destino = "./bin"
# ==============================

def borrar_split_files(carpeta_origen="./bin/split_files"):
    """
    Borra la carpeta de archivos divididos (split_files) sin afectar otros directorios.
    
    Args:
        carpeta_origen (str): ruta de la carpeta a eliminar (por defecto ./bin/split_files)
    """
    if os.path.exists(carpeta_origen) and os.path.isdir(carpeta_origen):
        shutil.rmtree(carpeta_origen)
        print(f"Carpeta eliminada: {carpeta_origen}")
    else:
        print(f"No existe la carpeta: {carpeta_origen}")


def drawOutput(dataI, dataQ, dataOut, samplesToGraphic):
    """Dibuja la salida del complejo combinado con I/Q"""
    samples = min(samplesToGraphic, len(dataI))
    index = np.arange(samples)

    plt.figure(figsize=(12, 6))
    plt.plot(index, dataI[:samples], 'b-', label='I (In-phase)', linewidth=1, alpha=0.8)
    plt.plot(index, dataQ[:samples], 'r-', label='Q (Quadrature)', linewidth=1, alpha=0.8)
    plt.title('Salida I/Q en tiempo')
    plt.xlabel('Muestras')
    plt.ylabel('Amplitud')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def splitFiles(inFileI, inFileQ, nElementsCount=4096, offset=6.0):
    """Procesa el archivo I y Q y los divide en archivos más pequeños"""
    print("Dividiendo archivos I/Q...")

    # Crear carpeta de salida si no existe
    Path(carpeta_origen).mkdir(parents=True, exist_ok=True)

    # Leer y procesar datos
    nCountI = np.fromfile(inFileI, dtype=np.complex64)
    nCountQ = np.fromfile(inFileQ, dtype=np.complex64)

    min_len = min(len(nCountI), len(nCountQ))
    nCountI = nCountI[:min_len]
    nCountQ = nCountQ[:min_len]

    # Extraer y combinar
    dataI = np.imag(nCountI) - offset
    dataQ = np.imag(nCountQ) - offset
    dataOut = dataI + 1j * dataQ

    if plot_en:
        drawOutput(dataI, dataQ, dataOut, samplesToGraphic)

    # Dividir en archivos más pequeños
    num_archivos = (min_len + nElementsCount - 1) // nElementsCount

    for i in range(num_archivos):
        inicio = i * nElementsCount
        fin = min((i + 1) * nElementsCount, min_len)

        chunk = dataOut[inicio:fin]
        nombre_archivo = Path(carpeta_origen) / f"chirp_{i}.bin"
        save_sc(nombre_archivo, chunk, fmt=fmt)

    print(f"Proceso completo. Total de archivos creados: {num_archivos}")
    return dataOut


def save_sc(filename, x, fmt='SC16_Q11'):
    """Guarda una señal compleja en formato SC8_Q7 o SC16_Q11."""
    if not np.iscomplexobj(x):
        raise ValueError("La señal debe ser compleja.")

    if fmt.upper() == 'SC16_Q11':
        dtype = np.int16
        frac_bits = 11
        max_val = (2**15 - 1) / (2**frac_bits)
    elif fmt.upper() == 'SC8_Q7':
        dtype = np.int8
        frac_bits = 7
        max_val = (2**7 - 1) / (2**frac_bits)
    else:
        raise ValueError("Formato no soportado. Usa 'SC16_Q11' o 'SC8_Q7'.")

    x = np.clip(x, -1, max_val)
    scale = 2**frac_bits

    real_i = np.round(np.real(x) * scale).astype(dtype)
    imag_i = np.round(np.imag(x) * scale).astype(dtype)

    interleaved = np.empty(2 * len(x), dtype=dtype)
    interleaved[0::2] = real_i
    interleaved[1::2] = imag_i

    interleaved.tofile(filename)
    return len(x), np.dtype(dtype).itemsize


def concatenar_bins(carpeta_origen, carpeta_destino, archivo_inicial):
    """Concatena los binarios divididos en uno solo."""
    # Crear carpeta destino si no existe
    os.makedirs(carpeta_destino, exist_ok=True)

    ruta_inicial = os.path.join(carpeta_origen, archivo_inicial)
    base, ext = os.path.splitext(ruta_inicial)

    match = re.match(r"^(.*)_(\d+)$", base)
    if not match:
        raise ValueError("El nombre debe terminar con _<número>, por ejemplo my_binario_0.bin")

    base_sin_indice = match.group(1)
    partes = []

    i = START_INDEX 
    while True:
        nombre = f"{base_sin_indice}_{i}{ext}"
        if not os.path.exists(nombre) or (i > END_INDEX and END_INDEX != -1):
            break
        partes.append(nombre)
        i += 1

    if not partes:
        raise FileNotFoundError(f"No se encontró ningún archivo que comience con {ruta_inicial}")

    tamaños = [os.path.getsize(p) for p in partes]
    if len(set(tamaños)) != 1:
        raise ValueError(f"Error: Los archivos no tienen el mismo tamaño ({tamaños})")

    salida = os.path.join(carpeta_destino, f"{os.path.basename(base_sin_indice)}_concat{ext}")
    with open(salida, "wb") as fout:
        for p in partes:
            with open(p, "rb") as fin:
                contenido = fin.read()
                fout.write(contenido)

    my_samples = tamaños[0] // (2 * (1 if fmt == 'SC8_Q7' else 2))
    print(f"{len(partes)} concatenaciones completadas de {tamaños[0]} bytes ({my_samples} samples). Archivo de salida: {salida}")
    return len(partes)


def export_to_header(chirps):
    """Crea config_override.h con la configuración del chirp generado"""
    header_path = "./src/config_override.h"
    dir_path = os.path.dirname(header_path)
    if not os.path.exists(dir_path):
        raise FileNotFoundError(f"No se encuentra el destino {header_path}")

    with open(header_path, "w") as f:
        f.write("// Archivo generado automaticamente\n")
        f.write("// Sobrescribe parametros del archivo bladerf_config.h\n\n")
        f.write(f"#ifndef CONFIG_OVERRIDE_H\n#define CONFIG_OVERRIDE_H\n\n")
        f.write("// Sobrescritura parametros\n")
        f.write(f"#undef SAMPLE_BITS\n#define SAMPLE_BITS  {8 if fmt=='SC8_Q7' else 16}\n\n")
        f.write(f"#undef SAMPLE_RATE\n#define SAMPLE_RATE  {int(fs)}\n\n")
        f.write(f'#undef CHIRP_FILE\n#define CHIRP_FILE  "chirp_concat.bin"\n\n')
        f.write(f'#undef NUM_CHIRPS\n#define NUM_CHIRPS  {chirps}\n\n')

        if nElementsCount < 8192:
            f.write(f"#undef TX_SAMPLES_PER_BUF\n#define TX_SAMPLES_PER_BUF  4096\n\n")
            f.write(f"#undef TX_NUM_BUFFERS\n#define TX_NUM_BUFFERS  2\n\n")
        elif nElementsCount < 16384:
            f.write(f"#undef TX_SAMPLES_PER_BUF\n#define TX_SAMPLES_PER_BUF  8192\n\n")
            f.write(f"#undef TX_NUM_BUFFERS\n#define TX_NUM_BUFFERS  2\n\n")
        else:
            raise ValueError("El chirp generado es demasiado largo para el buffer")
        

        f.write("#endif // CONFIG_OVERRIDE_H")

    print(f"Header generado en: {header_path}")


if __name__ == "__main__":
    try:
        # Crear estructura de carpetas si no existen
        Path(carpeta_destino).mkdir(parents=True, exist_ok=True)
        Path(carpeta_origen).mkdir(parents=True, exist_ok=True)

        splitFiles(inFileI, inFileQ, nElementsCount, OFFSET)
        num_chirps = concatenar_bins(carpeta_origen, carpeta_destino, "chirp_0.bin")
        export_to_header(num_chirps)
        if DELETE_SPLIT_FILES:
            borrar_split_files(carpeta_origen)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("FileNotFoundError")
    except Exception as e:
        print(f"Error durante el procesamiento: {e}")
