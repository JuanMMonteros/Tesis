import numpy as np
import matplotlib.pyplot as plt
import os

def load_sc(filename, fmt='SC16_Q11'):
    """Carga archivos en formato SC"""
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

def cargar_y_visualizar_chirps(filename, fmt, fs=60e6, t_chirp=10e-6, 
                              delay=10e-6, delay_calibracion=0.385e-6, N_chirps=5):
    """
    Carga archivo de chirps y genera gráficos
    """
    # Cargar señal
    señal_completa = load_sc(filename, fmt=fmt)
    
    # Calcular estructura
    samples_per_chirp = int(np.floor(t_chirp * fs))
    muestras_delay = int(np.floor((delay - delay_calibracion) * fs))
    muestras_por_chirp_completo = muestras_delay + samples_per_chirp
    
    # Crear matriz de chirps
    longitud_esperada = N_chirps * muestras_por_chirp_completo
    señal_completa = señal_completa[:longitud_esperada]
    matriz_chirps = señal_completa.reshape(N_chirps, muestras_por_chirp_completo)
    
    # Generar gráficos
    generar_graficos(matriz_chirps, muestras_delay, samples_per_chirp, fs, N_chirps)
    
    return matriz_chirps

def generar_graficos(matriz_chirps, muestras_delay, samples_per_chirp, fs, N_chirps):
    """Genera los dos gráficos principales"""
    
    muestras_totales = matriz_chirps.shape[1]
    t_chirp = np.arange(muestras_totales) / fs * 1e6  # Tiempo en microsegundos
    
    # GRÁFICO 1: Chirps individuales
    max_chirps_plot = min(5, N_chirps)
    
    fig, axes = plt.subplots(max_chirps_plot, 1, figsize=(12, 3*max_chirps_plot))
    if max_chirps_plot == 1:
        axes = [axes]
    
    for i in range(max_chirps_plot):
        chirp_completo = matriz_chirps[i]
        
        axes[i].plot(t_chirp, np.real(chirp_completo), 'b-', label='Real', linewidth=1)
        axes[i].plot(t_chirp, np.imag(chirp_completo), 'r-', label='Imag', linewidth=1, alpha=0.7)
        
        # Marcar región de delay
        if muestras_delay > 0:
            axes[i].axvspan(0, t_chirp[muestras_delay-1], alpha=0.2, color='gray', label='Delay')
        
        axes[i].set_ylabel(f'Chirp {i+1}')
        axes[i].grid(True, alpha=0.3)
        axes[i].legend(loc='upper right')
        
        if i == max_chirps_plot - 1:
            axes[i].set_xlabel('Tiempo (µs)')
    
    plt.suptitle(f'Matriz de {N_chirps} Chirps ({matriz_chirps.shape[1]} muestras por chirp)')
    plt.tight_layout()
    plt.show()
    
    # GRÁFICO 2: Vista superpuesta
    plt.figure(figsize=(12, 6))
    
    for i in range(min(5, N_chirps)):
        chirp_completo = matriz_chirps[i]
        offset = i * 2  # Desplazamiento vertical
        plt.plot(t_chirp, np.imag(chirp_completo) + offset, label=f'Chirp {i+1} Real')
    
    if muestras_delay > 0:
        plt.axvspan(0, t_chirp[muestras_delay-1], alpha=0.2, color='gray', label='Región Delay')
    
    plt.xlabel('Tiempo (µs)')
    plt.ylabel('Amplitud (con offset)')
    plt.title('Vista Superpuesta - Parte Real de Múltiples Chirps')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.show()

# ==============================
# CONFIGURACIÓN Y EJECUCIÓN
# ==============================
if __name__ == "__main__":
    # Parámetros (deben coincidir con generación)
    fs = 60e6
    t_chirp = 10e-6
    delay = 10e-6
    delay_calibracion = 0.385e-6
    fmt = 'SC16_Q11'
    N_chirps = 5

    # Ruta del archivo
    bin_dir = './bin'
    filename = f'{bin_dir}/chirp_{fmt}_{N_chirps}_phase_inc_5deg.bin'
    
    # Cargar y visualizar
    if os.path.exists(filename):
        matriz_chirps = cargar_y_visualizar_chirps(
            filename=filename,
            fmt=fmt,
            fs=fs,
            t_chirp=t_chirp,
            delay=delay,
            delay_calibracion=delay_calibracion,
            N_chirps=N_chirps
        )
        print(f"✅ Archivo cargado: {matriz_chirps.shape} (chirps × muestras)")
    else:
        print(f"❌ Archivo no encontrado: {filename}")