import numpy as np
import matplotlib.pyplot as plt
import os 

# ==============================
# Parámetros del chirp
# ==============================
f_start = -19e6
f_end   = 19e6
t_chirp = 10e-6
fs      = 60e6
fmt = 'SC16_Q11'    # Cambiar a 'SC8_Q7' o 'SC16_Q11'
plot_en = True
config_override_en = True

potencia = 1.0 # Potencia de la señal
phase = 2*np.pi*0/np.pi # Fase inicial en radianes
delay = 10e-6  # Retardo antes del chirp

delay_calibracion = 0.385e-6  # Retardo de calibración 

# ==============================
# Generacion Chirp
# ==============================
muestras_delay = int(np.floor( (delay - delay_calibracion) * fs))
amplitud = np.sqrt(potencia)
samples_per_chirp = int(np.floor(t_chirp * fs))

f1, f2 = f_start, f_end

# Vector de tiempo
t = np.arange(samples_per_chirp) / fs

# Tasa de chirp
k = (f2 - f1) / t_chirp

# Señal compleja
y_chirp = amplitud * np.exp(1j * 2 * np.pi * (f1 * t + 0.5 * k * t**2))* np.exp(1j * phase)

# ==============================
# Agregar retardo (ceros al inicio)
# ==============================
if muestras_delay > 0:
    y_delay = np.zeros(muestras_delay, dtype=complex)
    y_chirp = np.concatenate((y_delay, y_chirp))


# ==============================
# Funciones de guardado / carga
# ==============================
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
    return len(x), np.dtype(dtype).itemsize  # <-- devolvemos muestras y tamaño por elemento


def load_sc(filename, fmt='SC16_Q11'):
    """Carga una señal compleja en formato SC8_Q7 o SC16_Q11."""
    if fmt.upper() == 'SC16_Q11':
        dtype = np.int16
        frac_bits = 11
    elif fmt.upper() == 'SC8_Q7':
        dtype = np.int8
        frac_bits = 7
    else:
        raise ValueError("Formato no soportado. Usa 'SC16_Q11' o 'SC8_Q7'.")

    data = np.fromfile(filename, dtype=dtype)
    if len(data) % 2 != 0:
        raise ValueError("Archivo corrupto o longitud impar.")

    scale = 2**frac_bits
    real = data[0::2] / scale
    imag = data[1::2] / scale
    return real + 1j * imag


# ========================================
# Funciones de escritura config_override.h
# ========================================
def export_to_header():
    """
    Crea config_override.h con la configuracion del chirp generado
    """
    header_path = "./src/config_override.h"
    # Verificar que la carpeta destino exista
    dir_path = os.path.dirname(header_path)
    if not os.path.exists(dir_path):
        raise FileNotFoundError(f"No se encuentra el destino {header_path}")

    # Abrir archivo .h
    with open(header_path, "w") as f:
        f.write("// Archivo generado automaticamente\n")
        f.write("// Sobrescribe parametros del archivo bladerf_config.h\n\n")
        f.write(f"#ifndef CONFIG_OVERRIDE_H\n")
        f.write(f"#define CONFIG_OVERRIDE_H\n\n")
        f.write(f"// Sobrescritura parametros\n")
        
        f.write(f"#undef SAMPLE_BITS\n#define SAMPLE_BITS  {8 if fmt=='SC8_Q7' else 16}\n\n")
        f.write(f"#undef SAMPLE_RATE\n#define SAMPLE_RATE  {int(fs)}\n\n")
        f.write(f'#undef CHIRP_FILE\n#define CHIRP_FILE  "{filename}"\n\n')
        f.write(f'#undef NUM_CHIRPS\n#define NUM_CHIRPS  1\n\n')

        if(t_chirp * fs + muestras_delay < 8192):
            f.write(f"#undef TX_SAMPLES_PER_BUF\n#define TX_SAMPLES_PER_BUF  4096\n\n")
            f.write(f"#undef TX_NUM_BUFFERS\n#define TX_NUM_BUFFERS  2\n\n")
        elif(t_chirp * fs + muestras_delay < 16384):
            f.write(f"#undef TX_SAMPLES_PER_BUF\n#define TX_SAMPLES_PER_BUF  4096\n\n")
            f.write(f"#undef TX_NUM_BUFFERS\n#define TX_NUM_BUFFERS  4\n\n")
        else:
            raise ValueError("El chirp generado es demasiado largo para el buffer")

        f.write(f"#endif // CONFIG_OVERRIDE_H")

    print(f"Header generado en: {header_path}")


# ==============================
# Guardar, cargar y analizar
# ==============================
# Crear carpeta 'bin' si no existe
bin_dir = './bin'
if not os.path.exists(bin_dir):
    os.makedirs(bin_dir)
filename = f'{bin_dir}/chirp_{fmt}.bin'

num_samples, bytes_per_sample = save_sc(filename, y_chirp, fmt=fmt)
x_q = load_sc(filename, fmt=fmt)

# Calcular tamaño real del archivo
file_size = os.path.getsize(filename)
num_complex = file_size // (2 * bytes_per_sample)

# --- Calcular SNR ---
error = y_chirp - x_q
P_signal = np.mean(np.abs(y_chirp)**2)
P_error = np.mean(np.abs(error)**2)
SNR_dB = 10 * np.log10(P_signal / P_error)

# --- Mostrar resultados ---
print("\n--------------------------------------------------------------------")
print("REPORTE:\n")
print(f"Archivo: {filename}")
print(f"Formato: {fmt}")
print(f"Muestras complejas guardadas: {num_complex}")
print(f"Tamaño total del archivo: {file_size} bytes")
print(f"SNR de cuantización: {SNR_dB:.2f} dB")
print(f"Delay: {delay*1e6:.3f} µs")
print(f"Calibración delay: {delay_calibracion*1e6:.3f} µs")
if config_override_en:
    export_to_header()
else:
    print(f"Advertencia: autogeneración de config_override.h desactivada")
print("--------------------------------------------------------------------\n")

# ==============================
# Gráfica
# ==============================

if plot_en:
    t_total = np.arange(len(x_q)) / fs  # eje de tiempo con delay incluido
    plt.figure(figsize=(8,4))
    plt.plot(t_total * 1e6, np.real(x_q), label='Real')
    plt.plot(t_total * 1e6, np.imag(x_q), label='Imag')
    plt.grid(True)
    plt.xlabel("Tiempo (µs)")
    plt.ylabel("Amplitud")
    plt.title(f"Chirp cuantizado con delay ({fmt})")
    plt.legend()
    plt.show()