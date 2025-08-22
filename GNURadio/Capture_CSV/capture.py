import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants
import numpy as np
import csv

# Configuración de la placa BladeRF
args = dict(driver="bladerf")
sdr = SoapySDR.Device(args)

# Parámetros
sample_rate = 1e6  # 1 MS/s
freq = 2.45e9      # 2.45 GHz (ejemplo)
num_samples = 100000

# Configurar RX
sdr.setSampleRate(SOAPY_SDR_RX, 0, sample_rate)
sdr.setFrequency(SOAPY_SDR_RX, 0, freq)
sdr.setGain(SOAPY_SDR_RX, 0, 40)  # Ajustar según necesidad

# Crear buffer para recibir muestras I/Q
rx_buff = np.array([0]*num_samples, np.complex64)

# Activar el stream RX
rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rxStream)

# Leer muestras
sr = sdr.readStream(rxStream, [rx_buff], num_samples)

# Desactivar y limpiar stream
sdr.deactivateStream(rxStream)
sdr.closeStream(rxStream)

# Guardar en CSV (separando parte real e imaginaria)
with open('datos_bladerf.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['I', 'Q'])
    for sample in rx_buff:
        writer.writerow([sample.real, sample.imag])

print("Datos guardados en datos_bladerf.csv")

