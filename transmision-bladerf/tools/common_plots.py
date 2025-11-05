import numpy as np                           # Manejo de arreglos numéricos
import matplotlib.pyplot as plt              # Graficación
import os                                    # Manejo de rutas de archivos
from numpy.fft import fft, fftshift, fftfreq # Transformadas rápidas de Fourier
from scipy.signal import get_window, welch   # Ventanas y estimación de PSD

# Funciones para cargar y graficar señales complejas desde archivos binarios
def load_complex_signal(path, sample_bits=16):
    """Carga el archivo binario y devuelve la señal compleja."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"El archivo binario no se encontró en la ruta: {path}")

    dtype = np.int16 if sample_bits == 16 else np.int8
    data = np.fromfile(path, dtype=dtype)
    real = data[0::2]
    imag = data[1::2]
    signal = real + 1j * imag
    return signal

# Funciones de graficación
def plot_IQ(signal, fs):
    """Grafica la parte real e imaginaria de la señal en el tiempo."""
    num_samples = len(signal)
    time = np.arange(num_samples) / fs * 1e6  # Tiempo en µs

    plt.figure(figsize=(12, 6))

    plt.subplot(2, 1, 1)
    plt.plot(time, signal.real, color='blue')
    plt.title("Parte Real de la Señal")
    plt.xlabel("Tiempo (µs)")
    plt.ylabel("Amplitud")
    plt.grid()

    plt.subplot(2, 1, 2)
    plt.plot(time, signal.imag, color='red')
    plt.title("Parte Imaginaria de la Señal")
    plt.xlabel("Tiempo (µs)")
    plt.ylabel("Amplitud")
    plt.grid()

    plt.tight_layout()
    plt.show()

# Funciones de graficación del espectro
def plot_fft(signal, fs, alpha=0.05):
    """Calcula y grafica el espectro usando FFT y ventana Tukey."""
    N = len(signal)
    window = get_window(("tukey", alpha), N)
    spectrum = np.abs(fftshift(fft(signal * window)))
    freqs = fftshift(fftfreq(N, d=1/fs))
    spectrum_db = 20 * np.log10(spectrum / np.max(spectrum) + 1e-12)

    plt.figure(figsize=(10, 4))
    plt.plot(freqs / 1e6, spectrum_db, color='green')
    plt.title("Espectro de la Señal (FFT)")
    plt.xlabel("Frecuencia (MHz)")
    plt.ylabel("Magnitud (dB)")
    plt.grid()
    plt.tight_layout()
    plt.show()

# Funciones de graficación de la Densidad Espectral de Potencia
def plot_psd(signal, fs):
    """Calcula y grafica la Densidad Espectral de Potencia (PSD)."""
    nperseg = min(4096, len(signal))
    window = get_window("hann", nperseg)
    freqs, psd = welch(signal, fs=fs, window=window, nperseg=nperseg,
                       return_onesided=False, scaling='density')
    psd_dB = 10 * np.log10(np.abs(psd) + 1e-12)
    freqs = fftshift(freqs)
    psd_dB = fftshift(psd_dB)

    plt.figure(figsize=(10, 4))
    plt.plot(freqs / 1e6, psd_dB, color='purple')
    plt.title("Densidad Espectral de Potencia (PSD)")
    plt.xlabel("Frecuencia (MHz)")
    plt.ylabel("Potencia (dB/Hz)")
    plt.grid()
    plt.tight_layout()
    plt.show()


# Ejemplo de uso
signal=load_complex_signal("./bin/split_files/chirp_550.bin", sample_bits=16)
plot_IQ(signal, 38e6)
plot_fft(signal, 38e6)
plot_psd(signal, 38e6)