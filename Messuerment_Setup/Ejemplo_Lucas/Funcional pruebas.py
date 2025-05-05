# Script para capturar y analizar señales de chirp usando un analizador de espectro Tektronix RSA6114A.
# Genera tres vistas: DPX Spectrum, Time Overview y Pulse Trace, y calcula parámetros como duración, PRF, etc.

# --- Importación de librerías necesarias ---
import pyvisa  # Para comunicación con instrumentos vía VISA (Virtual Instrument Software Architecture)
import numpy as np  # Para operaciones numéricas y manejo de arreglos
import matplotlib.pyplot as plt  # Para graficar los resultados
import struct  # Para desempaquetar datos binarios recibidos del instrumento
import pandas as pd  # Para guardar datos en archivos CSV
import time  # Para agregar retrasos entre comandos
from scipy.signal import find_peaks  # Para detectar picos en los datos de Time Overview

# --- Configuración inicial de la conexión al instrumento ---
rm = pyvisa.ResourceManager()  # Crea un administrador de recursos para manejar conexiones VISA
instrument = None  # Variable para almacenar la conexión al instrumento (inicialmente None)

# Función para enviar comandos al instrumento y verificar su ejecución
def send_command(instr, command, wait_opc=True, delay=0.1):
    """
    Envía un comando al instrumento y espera su finalización si wait_opc es True.
    Args:
        instr: Objeto de conexión al instrumento.
        command (str): Comando SCPI a enviar.
        wait_opc (bool): Si True, espera confirmación de finalización con *OPC?.
        delay (float): Retraso en segundos después de enviar el comando.
    """
    print(f"Enviando: {command}")  # Muestra el comando que se está enviando
    instr.write(command)  # Envía el comando al instrumento
    time.sleep(delay)  # Espera un pequeño retraso para que el instrumento procese el comando
    if wait_opc:
        opc_response = instr.query('*OPC?')  # Consulta si el comando ha finalizado
        if opc_response.strip() == '1':
            print(f"Comando '{command}' completado.")
        else:
            print(f"Advertencia: No se recibió confirmación de finalización para '{command}'.")
    else:
        print(f"Comando '{command}' enviado sin esperar confirmación.")

# --- Bloque principal del script ---
try:
    # Establece conexión con el analizador de espectro Tektronix RSA6114A
    instrument = rm.open_resource('TCPIP::192.168.1.67::INSTR')  # Conecta al instrumento vía TCP/IP
    instrument.timeout = 120000  # Establece un timeout largo (120 segundos) para operaciones lentas
    send_command(instrument, '*CLS')  # Limpia el estado del instrumento
    send_command(instrument, '*IDN?', wait_opc=False)  # Solicita la identificación del instrumento
    idn = instrument.read().strip()  # Lee y muestra la identificación (por ejemplo, TEKTRONIX,RSA6114A)
    print(f"Identificación del instrumento: {idn}")
    send_command(instrument, ':INITiate:CONTinuous OFF')  # Desactiva el modo continuo para tomar mediciones únicas
    error_status = instrument.query(':SYSTem:ERRor?').strip()  # Verifica si hay errores después del comando
    print(f"Estado después de :INITiate:CONTinuous OFF: {error_status}")

    # --- Inicialización de variables para almacenar datos ---
    # Arreglos vacíos para almacenar los datos capturados de cada vista
    spectrum_data = np.array([])  # Datos de amplitud del espectro (DPX Spectrum)
    frequencies = np.array([])  # Frecuencias correspondientes al espectro
    time_overview_data = np.array([])  # Datos de amplitud en el dominio del tiempo (Time Overview)
    time_points = np.array([])  # Puntos temporales para Time Overview (en ms)
    pulse_data = np.array([])  # Datos de amplitud de un pulso individual (Pulse Trace)
    pulse_time = np.array([])  # Puntos temporales para Pulse Trace (en μs)

    # --- Captura de DPX Spectrum ---
    # DPX Spectrum muestra el espectro de frecuencia de la señal alrededor de 1.3 GHz
    try:
        print("\n--- Capturando DPX Spectrum ---")
        print("Configura: Frecuencia 1.3 GHz, Span 40 MHz, Atenuación 10 dB, RBW 1 MHz.")
        send_command(instrument, ':DISPlay:GENeral:MEASview:SELect DPSA')  # Selecciona la vista DPX Spectrum
        error_status = instrument.query(':SYSTem:ERRor?').strip()  # Verifica errores
        print(f"Estado después de :DISPlay:GENeral:MEASview:SELect DPSA: {error_status}")
        send_command(instrument, ':SENSe:DPSA:CLEar:RESults')  # Limpia los resultados anteriores
        send_command(instrument, ':SENSe:DPX:PLOT SPECtrum')  # Configura el modo de espectro
        send_command(instrument, ':SENSe:DPSA:FREQuency:CENTer 1.3E9')  # Frecuencia central en 1.3 GHz
        send_command(instrument, ':SENSe:DPSA:FREQuency:SPAN 40E6')  # Span de 40 MHz
        send_command(instrument, ':INPut:ATTenuation 10')  # Atenuación de entrada en 10 dB
        send_command(instrument, ':INPut:PREamp ON')  # Activa el preamplificador para mejorar la sensibilidad
        send_command(instrument, ':SENSe:DPSA:BANDwidth:RESolution 1E6')  # Resolución de ancho de banda (RBW) en 1 MHz
        # Desactiva las trazas no necesarias para optimizar la captura
        send_command(instrument, ':TRACe1:DPSA OFF')
        send_command(instrument, ':TRACe2:DPSA OFF')
        send_command(instrument, ':TRACe4:DPSA OFF')
        send_command(instrument, ':TRACe5:DPSA OFF')
        # Configura la traza 3 para promediar 50 mediciones y activarla
        send_command(instrument, ':TRACe3:DPSA:FUNCtion AVERage')
        send_command(instrument, ':TRACe3:DPSA:AVERage:COUNt 50')
        send_command(instrument, ':TRACe3:DPSA ON')
        error_status = instrument.query(':SYSTem:ERRor?').strip()  # Verifica errores después de configurar la traza
        print(f"Estado después de configurar Trace 3: {error_status}")
        send_command(instrument, ':INITiate:IMMediate', wait_opc=False)  # Inicia la medición
        time.sleep(90)  # Espera 90 segundos para que se complete el promediado
        opc_response = instrument.query('*OPC?').strip()  # Verifica que la operación haya terminado
        print(f"Operación completada (DPX Spectrum): {opc_response}")
        instrument.write(':FETCh:DPX:RESults:TRACe3?')  # Solicita los datos de la traza 3
        raw_response = instrument.read_raw()  # Lee los datos en formato binario
        print(f"Datos crudos de DPX Spectrum: {raw_response[:50]}...")
        # Procesa los datos binarios recibidos
        if raw_response[0] == ord('#'):  # Verifica que el formato sea correcto (inicia con #)
            num_digits = int(chr(raw_response[1]))  # Número de dígitos que indican la longitud de datos
            num_bytes = int(raw_response[2:2 + num_digits].decode())  # Longitud de los datos en bytes
            header_length = 2 + num_digits  # Longitud del encabezado
            data_bytes = raw_response[header_length:header_length + num_bytes]  # Extrae los datos
            spectrum_data = struct.unpack(f'<{num_bytes // 4}f', data_bytes)  # Convierte bytes a flotantes
            spectrum_data = np.array(spectrum_data)  # Convierte a arreglo NumPy
            # Genera un arreglo de frecuencias correspondiente a los datos (de 1280 MHz a 1320 MHz)
            frequencies = np.linspace(1.3e9 - 20e6, 1.3e9 + 20e6, len(spectrum_data))
            # Guarda los datos en un archivo CSV
            pd.DataFrame({'Frecuencia (Hz)': frequencies, 'Amplitud (dBm)': spectrum_data}).to_csv('dpx_spectrum.csv', index=False)
            print("Datos guardados en 'dpx_spectrum.csv'.")
        else:
            print("Formato de respuesta inesperado en DPX Spectrum.")
    except Exception as e:
        print(f"Error en DPX Spectrum: {e}")
       

    # --- Captura de Time Overview ---
    # Time Overview muestra la amplitud de la señal en el dominio del tiempo a lo largo de 10 ms
    try:
        print("\n--- Capturando Time Overview ---")
        print("Configurando la vista Time Overview...")
        send_command(instrument, ':DISPlay:PULSe:MEASview:NEW TOVerview')  # Selecciona la vista Time Overview
        send_command(instrument, ':INITiate:IMMediate', wait_opc=False)  # Inicia la medición
        opc_response = instrument.query('*OPC?').strip()  # Verifica que la operación haya terminado
        print(f"Operación completada (Time Overview): {opc_response}")
        instrument.write(':FETCh:TOVerview?')  # Solicita los datos de Time Overview
        raw_response = instrument.read_raw()  # Lee los datos en formato binario
        print(f"Datos crudos de Time Overview: {raw_response[:50]}...")
        if raw_response[0] == ord('#'):
            num_digits = int(chr(raw_response[1]))
            num_bytes = int(raw_response[2:2 + num_digits].decode())
            header_length = 2 + num_digits
            data_bytes = raw_response[header_length:header_length + num_bytes]
            time_overview_data = struct.unpack(f'<{num_bytes // 4}f', data_bytes)
            time_overview_data = np.array(time_overview_data)
            # Genera un arreglo de puntos temporales (de 0 a 10 ms)
            time_points = np.linspace(0, 10e-3, len(time_overview_data)) * 1e3  # Convierte a milisegundos
            # Guarda los datos en un archivo CSV
            pd.DataFrame({'Tiempo (ms)': time_points, 'Amplitud (dBm)': time_overview_data}).to_csv('time_overview.csv', index=False)
            print("Datos guardados en 'time_overview.csv'.")
        else:
            print("Formato de respuesta inesperado en Time Overview.")
    except Exception as e:
        print(f"Error en Time Overview: {e}")

    # --- Captura de Pulse Trace ---
    # Pulse Trace muestra un pulso individual en el dominio del tiempo durante 15 μs
    try:
        print("\n--- Capturando Pulse Trace ---")
        print("Configurando Pulse Trace: Umbral -4 dBm, Rango 15 μs, Reference Level 0 dBm.")
        send_command(instrument, ':SENSe:PULSe:THReshold -4')  # Establece el umbral para detectar pulsos en -4 dBm
        send_command(instrument, ':SENSe:PULSe:RANGe 15E-6')  # Rango de tiempo de 15 μs
        send_command(instrument, ':SENSe:PULSe:REFerence 0')  # Nivel de referencia en 0 dBm
        print("Configurando la vista Pulse Trace...")
        send_command(instrument, ':DISPlay:PULSe:MEASview:NEW TRACe')  # Selecciona la vista Pulse Trace
        send_command(instrument, ':INITiate:IMMediate', wait_opc=False)  # Inicia la medición
        opc_response = instrument.query('*OPC?').strip()  # Verifica que la operación haya terminado
        print(f"Operación completada (Pulse Trace): {opc_response}")
        instrument.write(':FETCh:PULSe:TRACe?')  # Solicita los datos de Pulse Trace
        raw_response = instrument.read_raw()  # Lee los datos en formato binario
        print(f"Datos crudos de Pulse Trace: {raw_response[:50]}...")
        if raw_response[0] == ord('#'):
            num_digits = int(chr(raw_response[1]))
            num_bytes = int(raw_response[2:2 + num_digits].decode())
            header_length = 2 + num_digits
            data_bytes = raw_response[header_length:header_length + num_bytes]
            pulse_data = struct.unpack(f'<{num_bytes // 4}f', data_bytes)
            pulse_data = np.array(pulse_data)
            # Genera un arreglo de puntos temporales (de 0 a 15 μs)
            pulse_time = np.linspace(0, 15e-6, len(pulse_data)) * 1e6  # Convierte a microsegundos
            # Filtrado suave para eliminar ruido extremo (valores fuera de -100 dBm a 20 dBm)
            valid_mask = (pulse_data >= -100) & (pulse_data <= 20)
            if np.any(valid_mask):
                pulse_data = pulse_data[valid_mask]  # Aplica el filtro
                pulse_time = pulse_time[valid_mask]  # Ajusta los tiempos correspondientes
                # Guarda los datos en un archivo CSV
                pd.DataFrame({'Tiempo (us)': pulse_time, 'Amplitud (dBm)': pulse_data}).to_csv('pulse_trace.csv', index=False)
                print("Datos guardados en 'pulse_trace.csv'.")
            else:
                print("No se encontraron datos válidos en Pulse Trace después de filtrar.")
                pulse_data = np.array([])
                pulse_time = np.array([])
        else:
            print("Formato de respuesta inesperado en Pulse Trace.")
    except Exception as e:
        print(f"Error en Pulse Trace: {e}")

    # --- Extracción de parámetros del chirp ---
    # Calcula parámetros como duración, amplitud, PRF, etc., a partir de los datos capturados
    try:
        print("\n--- Extrayendo parámetros del chirp ---")
        # Inicializa variables para los parámetros
        duration_us = 0  # Duración del pulso en μs
        amplitude_dbm = 0  # Amplitud máxima en dBm (de DPX Spectrum)
        min_freq = 0  # Frecuencia mínima en MHz
        max_freq = 0  # Frecuencia máxima en MHz
        central_freq = 0  # Frecuencia central en MHz
        bandwidth_mhz = 0  # Ancho de banda en MHz
        chirp_rate_mhz_per_us = 0  # Tasa de cambio de frecuencia en MHz/μs
        avg_power_dbm = 0  # Potencia promedio del pulso en dBm
        pri_ms = 0  # Intervalo entre pulsos (PRI) en ms
        prf_hz = 0  # Frecuencia de repetición de pulsos (PRF) en Hz

        # Calcula la duración del pulso a partir de Pulse Trace
        if len(pulse_data) > 0:
            threshold = np.max(pulse_data) - 10  # Umbral para detectar el pulso (máximo - 10 dB)
            pulse_mask = pulse_data > threshold  # Máscara para identificar el pulso
            if np.any(pulse_mask):
                start_idx = np.where(pulse_mask)[0][0]  # Índice de inicio del pulso
                end_idx = np.where(pulse_mask)[0][-1]  # Índice de fin del pulso
                duration_us = pulse_time[end_idx] - pulse_time[start_idx]  # Duración en μs
                print(f"Duración del chirp: {duration_us:.2f} μs")

        # Calcula la amplitud máxima a partir de DPX Spectrum
        if len(spectrum_data) > 0:
            amplitude_dbm = np.max(spectrum_data)  # Amplitud máxima en dBm
            print(f"Amplitud (dBm) desde DPX Spectrum: {amplitude_dbm:.2f} dBm")

        # Calcula la potencia promedio del pulso a partir de Pulse Trace
        if len(pulse_data) > 0 and np.any(pulse_mask):
            avg_power_dbm = np.mean(pulse_data[pulse_mask])  # Promedio de la amplitud durante el pulso
            print(f"Potencia promedio (dBm): {avg_power_dbm:.2f} dBm")

        # Calcula las frecuencias (mínima, máxima, central) y el ancho de banda a partir de DPX Spectrum
        if len(spectrum_data) > 0:
            noise_threshold = -70  # Umbral para filtrar ruido en el espectro
            valid_mask_spectrum = spectrum_data > noise_threshold
            if np.any(valid_mask_spectrum):
                spectrum_data_filtered = spectrum_data[valid_mask_spectrum]
                frequencies_filtered = frequencies[valid_mask_spectrum]
                freq_threshold = np.max(spectrum_data_filtered) - 10  # Umbral para identificar el pico
                freq_mask = spectrum_data_filtered > freq_threshold
                if np.any(freq_mask):
                    min_freq = frequencies_filtered[freq_mask][0] / 1e6  # Frecuencia mínima en MHz
                    max_freq = frequencies_filtered[freq_mask][-1] / 1e6  # Frecuencia máxima en MHz
                    central_freq = (min_freq + max_freq) / 2  # Frecuencia central
                    bandwidth_mhz = max_freq - min_freq  # Ancho de banda
                    # Calcula la tasa de cambio de frecuencia (si hay duración)
                    chirp_rate_mhz_per_us = bandwidth_mhz / duration_us if duration_us > 0 else 0
                    print(f"Frecuencia Mínima: {min_freq:.2f} MHz")
                    print(f"Frecuencia Máxima: {max_freq:.2f} MHz")
                    print(f"Frecuencia Central: {central_freq:.2f} MHz")
                    print(f"Ancho de banda: {bandwidth_mhz:.2f} MHz")
                    print(f"Tasa de cambio de frecuencia: {chirp_rate_mhz_per_us:.2f} MHz/μs")

        # Calcula el PRI (Pulse Repetition Interval) y PRF (Pulse Repetition Frequency) a partir de Time Overview
        if len(time_overview_data) > 0:
            threshold = -25  # Umbral para detectar picos en Time Overview
            distance = int((1.5 / 10) * len(time_overview_data))  # Distancia mínima entre picos (~1.5 ms)
            peaks, _ = find_peaks(time_overview_data, height=threshold, distance=distance)  # Detecta picos
            if len(peaks) > 1:
                intervals_ms = np.diff(time_points[peaks])  # Intervalos entre picos en ms
                pri_ms = np.mean(intervals_ms)  # PRI promedio
                prf_hz = 1000 / pri_ms  # PRF en Hz (1000 / PRI)
                print(f"Intervalo promedio entre pulsos (PRI): {pri_ms:.3f} ms")
                print(f"PRF: {prf_hz:.2f} Hz")
                # Grafica Time Overview con los picos detectados
                plt.figure(figsize=(10, 4))
                plt.plot(time_points, time_overview_data, label='Time Overview')  # Gráfica de Time Overview
                plt.plot(time_points[peaks], time_overview_data[peaks], "x", label='Picos detectados')  # Marca los picos
                plt.title('Time Overview con Picos Detectados')
                plt.xlabel('Tiempo (ms)')
                plt.ylabel('Amplitud (dBm)')
                plt.legend()
                plt.grid(True)
                plt.savefig('time_overview_peaks.png')  # Guarda el gráfico
                plt.show()

        # Guarda todos los parámetros calculados en un archivo CSV
        parameters = {
            'Duración (μs)': duration_us,
            'Amplitud (dBm)': amplitude_dbm,
            'Potencia Promedio (dBm)': avg_power_dbm,
            'Frecuencia Mínima (MHz)': min_freq,
            'Frecuencia Máxima (MHz)': max_freq,
            'Frecuencia Central (MHz)': central_freq,
            'Ancho de banda (MHz)': bandwidth_mhz,
            'Tasa de cambio de frecuencia (MHz/μs)': chirp_rate_mhz_per_us,
            'PRI (ms)': pri_ms,
            'PRF (Hz)': prf_hz
        }
        pd.DataFrame([parameters]).to_csv('chirp_parameters.csv', index=False)
        print("Parámetros guardados en 'chirp_parameters.csv'.")

    except Exception as e:
        print(f"Error al extraer parámetros: {e}")

    # --- Generación de gráficos con las tres vistas ---
    # Crea un gráfico con tres subplots: DPX Spectrum, Time Overview y Pulse Trace
    plt.figure(figsize=(10, 12))

    # Subplot para DPX Spectrum
    plt.subplot(3, 1, 1)
    if len(spectrum_data) > 0:
        plt.plot(frequencies / 1e6, spectrum_data, label='DPX Spectrum')  # Grafica el espectro
        plt.title('DPX Spectrum')
        plt.xlabel('Frecuencia (MHz)')
        plt.ylabel('Amplitud (dBm)')
        plt.grid(True)
        plt.legend()
    else:
        plt.text(0.5, 0.5, "No se capturaron datos en DPX Spectrum", ha='center', va='center')  # Mensaje si no hay datos

    # Subplot para Time Overview
    plt.subplot(3, 1, 2)
    if len(time_overview_data) > 0:
        plt.plot(time_points, time_overview_data)  # Grafica Time Overview
        plt.title('Time Overview')
        plt.xlabel('Tiempo (ms)')
        plt.ylabel('Amplitud (dBm)')
        plt.grid(True)
    else:
        plt.text(0.5, 0.5, "No se capturaron datos en Time Overview", ha='center', va='center')

    # Subplot para Pulse Trace
    plt.subplot(3, 1, 3)
    if len(pulse_data) > 0:
        plt.plot(pulse_time, pulse_data)  # Grafica Pulse Trace
        plt.title('Pulse Trace')
        plt.xlabel('Tiempo (us)')
        plt.ylabel('Amplitud (dBm)')
        plt.grid(True)
    else:
        plt.text(0.5, 0.5, "No se capturaron datos en Pulse Trace", ha='center', va='center')

    plt.tight_layout()  # Ajusta el diseño para evitar solapamiento
    plt.savefig('grafica_tres_ventanas.png')  # Guarda el gráfico
    plt.show()

except Exception as e:
    print(f"Error general: {e}")

finally:
    # Cierra la conexión al instrumento y libera recursos
    if instrument is not None:
        instrument.close()  # Cierra la conexión al instrumento
    rm.close()  # Cierra el administrador de recursos
    print("Conexión cerrada correctamente.")
