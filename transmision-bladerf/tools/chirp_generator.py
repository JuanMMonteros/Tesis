import numpy as np
import matplotlib.pyplot as plt
import os

def load_sc(filename, fmt='SC16_Q11'):
    """Función para cargar archivos en formato SC"""
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

def analizar_chirps_binario(filename, fmt, fs=60e6, t_chirp=10e-6, delay=10e-6, delay_calibracion=0.385e-6, N_chirps=None):
    """
    Analiza el archivo binario y crea matriz de chirps
    
    Parameters:
    - filename: ruta del archivo
    - fmt: formato del archivo ('SC16_Q11' o 'SC8_Q7')
    - fs: frecuencia de muestreo
    - t_chirp: duración del chirp en segundos
    - delay: delay antes de cada chirp
    - delay_calibracion: delay de calibración
    - N_chirps: número de chirps (si None, se calcula automáticamente)
    """
    
    # Cargar señal desde archivo binario
    señal_completa = load_sc(filename, fmt=fmt)
    
    # Calcular parámetros
    samples_per_chirp = int(np.floor(t_chirp * fs))
    muestras_delay = int(np.floor((delay - delay_calibracion) * fs))
    muestras_por_chirp_completo = muestras_delay + samples_per_chirp
    
    print(f"=== PARÁMETROS DETECTADOS ===")
    print(f"Muestras por chirp (sin delay): {samples_per_chirp}")
    print(f"Muestras de delay: {muestras_delay}")
    print(f"Muestras por chirp completo: {muestras_por_chirp_completo}")
    print(f"Longitud señal completa: {len(señal_completa)}")
    
    # Determinar número de chirps si no se especifica
    if N_chirps is None:
        N_chirps = len(señal_completa) // muestras_por_chirp_completo
        print(f"Número de chirps detectados: {N_chirps}")
    
    # Verificar que la longitud sea consistente
    longitud_esperada = N_chirps * muestras_por_chirp_completo
    if len(señal_completa) < longitud_esperada:
        raise ValueError(f"La señal es más corta de lo esperado. Esperado: {longitud_esperada}, Obtenido: {len(señal_completa)}")
    
    # Recortar señal si es necesario
    señal_completa = señal_completa[:longitud_esperada]
    
    # Crear matriz donde cada fila es un chirp completo (delay + chirp)
    matriz_chirps = señal_completa.reshape(N_chirps, muestras_por_chirp_completo)
    
    return matriz_chirps, muestras_delay, samples_per_chirp, fs

def plot_matriz_chirps(matriz_chirps, muestras_delay, samples_per_chirp, fs, max_chirps_plot=5):
    """
    Grafica los chirps en forma de matriz
    """
    N_chirps, muestras_totales = matriz_chirps.shape
    t_chirp = np.arange(muestras_totales) / fs * 1e6  # Tiempo en microsegundos
    
    # Limitar número de chirps a plotear si hay muchos
    chirps_a_plotear = min(N_chirps, max_chirps_plot)
    
    # Crear figura con subplots
    fig, axes = plt.subplots(chirps_a_plotear, 1, figsize=(12, 3*chirps_a_plotear))
    if chirps_a_plotear == 1:
        axes = [axes]
    
    for i in range(chirps_a_plotear):
        chirp_completo = matriz_chirps[i]
        
        # Separar en delay y chirp
        parte_delay = chirp_completo[:muestras_delay]
        parte_chirp = chirp_completo[muestras_delay:]
        
        # Plotear
        axes[i].plot(t_chirp, np.real(chirp_completo), 'b-', label='Parte Real', linewidth=1)
        axes[i].plot(t_chirp, np.imag(chirp_completo), 'r-', label='Parte Imag', linewidth=1, alpha=0.7)
        
        # Marcar región de delay
        if muestras_delay > 0:
            axes[i].axvspan(0, t_chirp[muestras_delay-1], alpha=0.2, color='gray', label='Delay')
        
        axes[i].set_ylabel(f'Chirp {i+1}')
        axes[i].grid(True, alpha=0.3)
        axes[i].legend(loc='upper right')
        
        if i == chirps_a_plotear - 1:
            axes[i].set_xlabel('Tiempo (µs)')
    
    plt.suptitle(f'Matriz de Chirps - {N_chirps} chirps completos (Delay + Chirp)')
    plt.tight_layout()
    plt.show()
    
    # Plot resumen de todos los chirps
    plt.figure(figsize=(12, 6))
    for i in range(chirps_a_plotear):
        chirp_completo = matriz_chirps[i]
        offset = i * 2  # Desplazamiento vertical para visualización
        plt.plot(t_chirp, np.real(chirp_completo) + offset, label=f'Chirp {i+1} Real')
    
    if muestras_delay > 0:
        plt.axvspan(0, t_chirp[muestras_delay-1], alpha=0.2, color='gray', label='Región Delay')
    
    plt.xlabel('Tiempo (µs)')
    plt.ylabel('Amplitud (con offset)')
    plt.title('Vista Superpuesta de Chirps - Parte Real')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.show()

def analizar_ceros_delay(matriz_chirps, muestras_delay):
    """
    Analiza específicamente la región de ceros (delay)
    """
    print("\n=== ANÁLISIS DE REGIÓN DELAY ===")
    
    for i in range(min(3, matriz_chirps.shape[0])):  # Analizar primeros 3 chirps
        region_delay = matriz_chirps[i, :muestras_delay]
        
        # Verificar si son realmente ceros
        max_valor = np.max(np.abs(region_delay))
        promedio_real = np.mean(np.real(region_delay))
        promedio_imag = np.mean(np.imag(region_delay))
        
        print(f"Chirp {i+1}:")
        print(f"  - Muestras en delay: {len(region_delay)}")
        print(f"  - Valor máximo (abs): {max_valor:.6f}")
        print(f"  - Promedio parte real: {promedio_real:.6f}")
        print(f"  - Promedio parte imag: {promedio_imag:.6f}")
        
        if max_valor < 1e-10:
            print(f"  ✓ Región delay: CEROS PERFECTOS")
        elif max_valor < 0.01:
            print(f"  ≈ Región delay: CEROS APROXIMADOS (máximo: {max_valor:.6f})")
        else:
            print(f"  ! Región delay: POSIBLE ERROR (máximo: {max_valor:.6f})")

# ==============================
# PARÁMETROS (deben coincidir con los de generación)
# ==============================
fs = 60e6
t_chirp = 10e-6
delay = 10e-6
delay_calibracion = 0.385e-6
fmt = 'SC16_Q11'
N_chirps = 10

# ==============================
# EJECUCIÓN PRINCIPAL
# ==============================
if __name__ == "__main__":
    # Ruta del archivo
    bin_dir = './bin'
    filename = f'{bin_dir}/chirp_{fmt}_{N_chirps}.bin'
    
    if not os.path.exists(filename):
        print(f"Error: No se encuentra el archivo {filename}")
        exit(1)
    
    try:
        # Cargar y crear matriz de chirps
        matriz_chirps, muestras_delay, samples_chirp, fs = analizar_chirps_binario(
            filename, fmt, fs, t_chirp, delay, delay_calibracion, N_chirps
        )
        
        # Mostrar información general
        print(f"\n=== INFORMACIÓN GENERAL ===")
        print(f"Dimensiones matriz: {matriz_chirps.shape} (chirps × muestras)")
        print(f"Duración total por chirp: {(muestras_delay + samples_chirp)/fs*1e6:.2f} µs")
        print(f"  - Delay: {muestras_delay/fs*1e6:.2f} µs")
        print(f"  - Chirp: {samples_chirp/fs*1e6:.2f} µs")
        
        # Analizar región de ceros
        analizar_ceros_delay(matriz_chirps, muestras_delay)
        
        # Graficar
        plot_matriz_chirps(matriz_chirps, muestras_delay, samples_chirp, fs, max_chirps_plot=5)
        
    except Exception as e:
        print(f"Error: {e}")