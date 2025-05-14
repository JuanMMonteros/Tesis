import pyvisa  # Para comunicación con instrumentos vía VISA
import time  # Para agregar retrasos entre comandos
import sys
import pandas as pd  # Para guardar datos en archivos CSV
import struct  # Para desempaquetar datos binarios recibidos del instrumento
import numpy as np  # Para operaciones numéricas y manejo de arreglos
import matplotlib.pyplot as plt

# --- Configuración inicial de la conexión al instrumento ---
rm = pyvisa.ResourceManager()  # Crea un administrador de recursos para manejar conexiones VISA
instrument = None  # Variable para almacenar la conexión al instrumento (inicialmente None)

def ploter(archivo):

    # Leer la primera línea como título (correctamente, sin confundirla con encabezado)
    with open(archivo_csv, 'r', encoding='utf-8') as f:
        titulo = f.readline().strip()

    # Leer el resto del CSV usando la segunda línea como header
    df = pd.read_csv(archivo_csv, skiprows=1)

    # Verificar columnas
    x_label = df.columns[0]
    y_label = df.columns[1]

    # Graficar
    plt.figure(figsize=(12, 6))
    plt.plot(df[x_label], df[y_label], color='blue', linewidth=1)
    plt.xlabel(x_label, fontsize=12)
    plt.ylabel(y_label, fontsize=12)
    plt.title(titulo, fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()  

# Función para enviar comandos al instrumento y verificar su ejecución
def send_command(instr, command, wait_opc=True, delay=0.1):
    """
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

def instrument_config(instrument, csv_file):
    """
    Configura el instrumento según los comandos y parámetros definidos en un archivo CSV.

    Args:
        instrument: Objeto de conexión al instrumento.
        csv_file (str): Ruta al archivo CSV que contiene la configuración.
    """
    try:
        df = pd.read_csv(csv_file, encoding='utf-8-sig')  # Lectura robusta con manejo de BOM

        # Validar columnas requeridas
        columnas_requeridas = ['Tipo', 'Comando', 'Parametro', 'Descripcion', 'Delay']
        if not all(col in df.columns for col in columnas_requeridas):
            print(f"Error: Faltan columnas en el CSV. Se esperaban: {columnas_requeridas}")
            print(f"Columnas encontradas: {list(df.columns)}")
            return 1

        # Iterar por cada fila como diccionario
        for _, row in df.iterrows():
            try:
                tipo = row['Tipo']
                comando = row['Comando']
                parametro = row['Parametro']
                descripcion = row['Descripcion']
                delay = row['Delay']

                # Aplica delay si se especifica
                try:
                    delay_value = float(delay) if pd.notna(delay) else 0
                except ValueError:
                    print(f"Delay inválido en línea: {row.to_dict()}")
                    delay_value = 0

                if delay_value > 0:
                    print(f"Esperando {delay_value} segundos...")
                    time.sleep(delay_value)

                if tipo == 'Print':
                    print(descripcion)
                elif tipo == 'Comando':
                    comando_completo = f"{comando} {parametro}" if pd.notna(parametro) else comando
                    send_command(instrument, comando_completo)
                elif tipo == 'VerificarError':
                    error_status = instrument.query(comando).strip()
                    print(f"Estado de error ({descripcion}): {error_status}")
                elif tipo == 'VerificarOPC':
                    opc_response = instrument.query(comando).strip()
                    print(f"Estado OPC ({descripcion}): {opc_response}")
                elif tipo == 'Espera':
                    continue
                else:
                    print(f"Tipo de instrucción desconocido: {tipo}")

            except Exception as e:
                print(f"Error procesando línea: {row.to_dict()} - {str(e)}")
                try:
                    last_error = instrument.query(':SYSTem:ERRor?').strip()
                    print(f"Último error del instrumento: {last_error}")
                except pyvisa.VisaIOError:
                    print("No se pudo obtener el último error del instrumento (error de VISA).")
                except Exception as e_inner:
                    print(f"No se pudo obtener el último error del instrumento: {e_inner}")
                return 1

        print("Configuración completada")
        return 0

    except FileNotFoundError:
        print(f"Error: El archivo de configuración '{csv_file}' no se encontró.")
        return 1
    except Exception as e:
        print(f"Error al procesar el archivo de configuración: {e}")
        return 1


def DPX(instrument, directorio, plot):
    # --- Inicialización de variables para almacenar datos ---
    spectrum_data = np.array([])  # Datos de amplitud del espectro (DPX Spectrum)
    frequencies = np.array([])  # Frecuencias correspondientes al espectro
    try:
        if instrument_config(instrument, "config_dpx.csv") == 0: # Llama a la funcion y verifica que no hubo error
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

                i = 1
                while os.path.exists(os.path.join(directorio, f'DPX_{i}.csv')):  # Verifica si el archivo ya existe
                    i += 1  # Incrementa el número

                filename = f'DPX_{i}.csv'
                output_path = os.path.join(directorio, filename)
                # Guarda los datos en un archivo CSV
                pd.DataFrame({'Frecuencia (Hz)': frequencies, 'Amplitud (dBm)': spectrum_data}).to_csv(output_path, index=False)
                print(f"Datos guardados en '{output_path}'.")

                if plot:
                    ploter(output_path)
        else:
            print("Formato de respuesta inesperado en DPX Spectrum.")
        
        return f"Medicion Exitosa"

    except Exception as e:
        return f"Error en DPX Spectrum: {e}"  # Solicitar datos


def PVT(instrument, directorio, plot):
    # --- Inicialización de variables para almacenar datos ---
    phase_data = np.array([])  # Datos de fase
    time = np.array([])  # vector de tiempo
    try:
        if instrument_config(instrument, "config_PVT.csv") == 0: # Llama a la funcion y verifica que no hubo error
        
            instrument.write(':FETCh:PVHTime?')  # Solicita los datos de phase vs time 
            raw_response = instrument.read_raw()  # Lee los datos en formato binario
            print(f"Datos crudos de Phase vs Time {raw_response[:50]}...")

            # Procesa los datos binarios recibidos
            if raw_response[0] == ord('#'):  # Verifica que el formato sea correcto (inicia con #)
                num_digits = int(chr(raw_response[1]))  # Número de dígitos que indican la longitud de datos
                num_bytes = int(raw_response[2:2 + num_digits].decode())  # Longitud de los datos en bytes
                header_length = 2 + num_digits  # Longitud del encabezado
                data_bytes = raw_response[header_length:header_length + num_bytes]  # Extrae los datos
                phase_data = struct.unpack(f'<{num_bytes // 4}f', data_bytes)  # Convierte bytes a flotantes
                phase_data = np.array(phase_data)  # Convierte a arreglo NumPy

                # Genera un arreglo de time# Genera un arreglo de puntos temporales (de 0 a 10 ms)
                time_points = np.linspace(0, 10e-3, len(phase_data)) * 1e3  # Convierte a milisegundos

                # Busca el próximo número disponible para el archivo
                i = 1
                while os.path.exists(os.path.join(directorio, f'PVTime_{i}.csv')):  # Verifica si el archivo ya existe
                    i += 1  # Incrementa el número

                filename = f'PVTime_{i}.csv'
                output_path = os.path.join(directorio, filename)

                # Guarda los datos en un archivo CSV
                pd.DataFrame({'Time (ms)': time_points, 'Phase (º)': phase_data}).to_csv(output_path, index=False)
                print(f"Datos guardados en '{output_path}'.")

                if plot:
                    ploter(output_path)
            else:
                print("Formato de respuesta inesperado en Phase vs Time.")
        return f"Medicion Exitosa"

    except Exception as e:
        return f"Error en Phase vs Time: {e}"  # Solicitar datos
  
def TimeOverview(instrument, directorio, plot):
    # --- Inicialización de variables para almacenar datos ---
    time_overview_data = np.array([])  # Datos de fase
    time = np.array([])  # vector de tiempo
    try:
        print("\n--- Capturando Time Overview ---")
        print("Configurando la vista Time Overview...")
        send_command(instrument, ':DISPlay:PULSe:MEASview:NEW TOVerview')  # Selecciona la vista Time Overview
        send_command(instrument, ':INITiate:IMMediate', wait_opc=False)  # Inicia la medición
        opc_response = instrument.query('*OPC?').strip()  # Verifica que la operación haya terminado
        print(f"Operación completada (Time Overview): {opc_response}")

        instrument.write(':FETCh:TOverview?')  # Solicita los datos de phase vs time 
        raw_response = instrument.read_raw()  # Lee los datos en formato binario
        print(f"Datos crudos de TimeOverview {raw_response[:50]}...")

        # Procesa los datos binarios recibidos
        if raw_response[0] == ord('#'):  # Verifica que el formato sea correcto (inicia con #)
            num_digits = int(chr(raw_response[1]))  # Número de dígitos que indican la longitud de datos
            num_bytes = int(raw_response[2:2 + num_digits].decode())  # Longitud de los datos en bytes
            header_length = 2 + num_digits  # Longitud del encabezado
            data_bytes = raw_response[header_length:header_length + num_bytes]  # Extrae los datos
            phase_data = struct.unpack(f'<{num_bytes // 4}f', data_bytes)  # Convierte bytes a flotantes
            phase_data = np.array(phase_data)  # Convierte a arreglo NumPy

            # Genera un arreglo de time# Genera un arreglo de puntos temporales (de 0 a 10 ms)
            time_points = np.linspace(0, 10e-3, len(phase_data)) * 1e3  # Convierte a milisegundos

            # Busca el próximo número disponible para el archivo
            i = 1
            while os.path.exists(os.path.join(directorio, f'TimeOverview_{i}.csv')):  # Verifica si el archivo ya existe
                i += 1  # Incrementa el número

            filename = f'TimeOverview_{i}.csv'
            output_path = os.path.join(directorio, filename)

            # Guarda los datos en un archivo CSV
            pd.DataFrame({'Time (ms)': time_points, 'Amplitud (dBm)': time_overview_data}).to_csv(output_path, index=False)
            print(f"Datos guardados en '{output_path}'.")

            if plot:
                ploter(output_path)
        else:
            print("Formato de respuesta inesperado en TimeOverview.")
        return f"Medicion Exitosa"

    except Exception as e:
        return f"Error en Phase vs Time: {e}"  # Solicitar datos

