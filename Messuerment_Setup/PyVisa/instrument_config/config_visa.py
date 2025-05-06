import pyvisa  # Para comunicación con instrumentos vía VISA
import time  # Para agregar retrasos entre comandos
import sys
import pandas as pd  # Para guardar datos en archivos CSV
import struct  # Para desempaquetar datos binarios recibidos del instrumento
import numpy as np  # Para operaciones numéricas y manejo de arreglos


# --- Configuración inicial de la conexión al instrumento ---
rm = pyvisa.ResourceManager()  # Crea un administrador de recursos para manejar conexiones VISA
instrument = None  # Variable para almacenar la conexión al instrumento (inicialmente None)

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

    if instrument_config(instrument, "config.csv") == 0: # Llama a la funcion y verifica que no hubo error
        try:
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
            print(f"Error en DPX Spectrum: {e}")  # Solicitar datos
    else:
        print('Error en la configuracion')

except Exception as e:
    print(f"Error general: {e}")

finally:
    # Cierra la conexión al instrumento y libera recursos
    if instrument is not None:
        instrument.close()  # Cierra la conexión al instrumento
    rm.close()  # Cierra el administrador de recursos
    print("Conexión cerrada correctamente.")
