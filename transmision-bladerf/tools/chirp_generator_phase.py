import numpy as np
import matplotlib.pyplot as plt
import os 

# ==============================
# Parámetros del chirp
# ==============================
f_start = -5e6
f_end   = 5e6
t_chirp = 10e-6
fs      = 60e6
fmt = 'SC16_Q11'    # Cambiar a 'SC8_Q7' o 'SC16_Q11'
plot_en = False
config_override_en = True

potencia = 1.0       # Potencia de la señal
phase = 0            # Fase inicial en radianes
delay =0e-6        # Retardo antes del chirp
delay_calibracion = 0#0.385e-6  # Retardo de calibración 

# ==============================
# Parámetros avanzados
# ==============================
N_chirps = 5  # Número de chirps a generar
phase_increment_deg = 72  # Incremento de fase en grados por chirp
chirp_direction = 'down'  # 'up' o 'down' - Dirección del chirp

# ==============================
# Generacion Chirp
# ==============================
samples_per_chirp = int(np.floor(t_chirp * fs))
muestras_delay = int(np.floor((delay - delay_calibracion) * fs))
amplitud = np.sqrt(potencia)

# Vector de tiempo para un chirp
t = np.arange(samples_per_chirp) / fs

# Configurar frecuencias según dirección
if chirp_direction.lower() == 'down':
    # Para down chirp: frecuencia comienza alta y termina baja
    f_initial = f_end
    f_final = f_start
    chirp_type_name = 'Down-Chirp'
else:  # 'up' por defecto
    # Para up chirp: frecuencia comienza baja y termina alta
    f_initial = f_start
    f_final = f_end
    chirp_type_name = 'Up-Chirp'

# Tasa de chirp
k = (f_final - f_initial) / t_chirp

# Generar chirps con fase incremental
chirps_list = []
for i in range(N_chirps):
    # Calcular fase para este chirp (convertir grados a radianes)
    current_phase = phase + np.deg2rad(i * phase_increment_deg)
    
    # Generar chirp con fase específica
    chirp = amplitud * np.exp(1j * 2 * np.pi * (f_initial * t + 0.5 * k * t**2)) * np.exp(1j * current_phase)
    
    # Agregar retardo al inicio
    if muestras_delay > 0:
        chirp = np.concatenate((np.zeros(muestras_delay, dtype=complex), chirp))
    
    chirps_list.append(chirp)

# Concatenar todos los chirps
y_chirps = np.concatenate(chirps_list)

# ==============================
# Funciones de guardado / carga
# ==============================
def save_sc(filename, x, fmt='SC16_Q11'):
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

def load_sc(filename, fmt='SC16_Q11'):
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
        f.write(f'#undef NUM_CHIRPS\n#define NUM_CHIRPS  {N_chirps}\n\n')

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
bin_dir = './bin'
if not os.path.exists(bin_dir):
    os.makedirs(bin_dir)
filename = f'{bin_dir}/chirp_{fmt}_phase_sweep.bin'

num_samples, bytes_per_sample = save_sc(filename, y_chirps, fmt=fmt)
x_q = load_sc(filename, fmt=fmt)

# Calcular tamaño real del archivo
file_size = os.path.getsize(filename)
num_complex = file_size // (2 * bytes_per_sample)

# --- Calcular SNR ---
error = y_chirps - x_q
P_signal = np.mean(np.abs(y_chirps)**2)
P_error = np.mean(np.abs(error)**2)
SNR_dB = 10 * np.log10(P_signal / P_error)

# --- Mostrar resultados ---
print("\n--------------------------------------------------------------------")
print("REPORTE CON CONTROL DE DIRECCIÓN Y FASE:")
print(f"Archivo: {filename}")
print(f"Formato: {fmt}")
print(f"Tipo de chirp: {chirp_type_name}")
print(f"Muestras complejas guardadas: {num_complex}")
print(f"Tamaño total del archivo: {file_size} bytes")
print(f"SNR de cuantización: {SNR_dB:.2f} dB")
print(f"Delay: {delay*1e6:.3f} µs")
print(f"Calibración delay: {delay_calibracion*1e6:.3f} µs")
print(f"Incremento de fase por chirp: {phase_increment_deg}°")
print(f"Frecuencia inicial: {f_initial/1e6:.1f} MHz")
print(f"Frecuencia final: {f_final/1e6:.1f} MHz")
if config_override_en:
    export_to_header()
else:
    print(f"Advertencia: autogeneración de config_override.h desactivada")
print("--------------------------------------------------------------------\n")

# ==============================
# Gráfica de los chirps generados
# ==============================
if plot_en:
    # Calcular parámetros para visualización
    muestras_por_chirp_completo = muestras_delay + samples_per_chirp
    matriz_chirps = y_chirps.reshape(N_chirps, muestras_por_chirp_completo)
    t_chirp = np.arange(muestras_por_chirp_completo) / fs * 1e6  # Tiempo en microsegundos
    
    # Vista superpuesta
    plt.figure(figsize=(12, 6))
    
    for i in range(N_chirps):
        chirp_completo = matriz_chirps[i]
        offset = i * 2  # Desplazamiento vertical para visualización
        current_phase_deg = phase + i * phase_increment_deg
        plt.plot(t_chirp, np.real(chirp_completo) + offset, label=f'Chirp {i+1} (φ={current_phase_deg:.1f}°)')
    
    if muestras_delay > 0:
        plt.axvspan(0, t_chirp[muestras_delay-1], alpha=0.2, color='gray', label='Región Delay')
    
    plt.xlabel('Tiempo (µs)')
    plt.ylabel('Amplitud (con offset)')
    plt.title(f'Vista Superpuesta - {chirp_type_name}s (Δφ={phase_increment_deg}°)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.show()
    
    # GRÁFICO 3: Análisis de frecuencia instantánea
    plt.figure(figsize=(12, 4))
    
    # Calcular frecuencia instantánea para el primer chirp (sin delay)
    chirp_sin_delay = matriz_chirps[0, muestras_delay:]
    phase_instant = np.unwrap(np.angle(chirp_sin_delay))
    freq_instant = np.diff(phase_instant) / (2 * np.pi) * fs / 1e6  # MHz
    
    t_freq = np.arange(len(freq_instant)) / fs * 1e6  # µs
    
    plt.plot(t_freq, freq_instant, 'g-', linewidth=2, label='Frecuencia instantánea')
    plt.axhline(y=f_initial/1e6, color='r', linestyle='--', label=f'f_inicial = {f_initial/1e6:.1f} MHz')
    plt.axhline(y=f_final/1e6, color='b', linestyle='--', label=f'f_final = {f_final/1e6:.1f} MHz')
    
    plt.xlabel('Tiempo (µs)')
    plt.ylabel('Frecuencia (MHz)')
    plt.title(f'Análisis de Frecuencia Instantánea - {chirp_type_name}')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.show()