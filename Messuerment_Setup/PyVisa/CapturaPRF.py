# --- Importación de librerías necesarias ---
import pyvisa  # Para comunicación con instrumentos vía VISA (Virtual Instrument Software Architecture)
import numpy as np  # Para operaciones numéricas y manejo de arreglos
import pandas as pd  # Para guardar datos en archivos CSV
import time  # Para agregar retrasos entre comandos
import sys # Para manejar argumentos de línea de comandos y salida del programa
import struct # Para manejar datos binarios

if len(sys.argv) > 1:
    ip = sys.argv[1]
else:
    print('PasAr la dirección IP del instrumento como argumento de línea de comandos.')
    sys.exit(0)

    
# --- Configuración inicial de la conexión al instrumento ---
rm = pyvisa.ResourceManager()  # Crea un administrador de recursos para manejar conexiones VISA
instrument = None  # Variable para almacenar la conexión al instrumento (inicialmente None)



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

def initialize_instrument():
    """
    Inicializa la conexión con el instrumento.
    """
    global instrument, ip, rm
            # Conecta al instrumento usando su dirección VISA
    instrument = rm.open_resource('TCPIP0::' + ip + '::INSTR')
    # Configura el tiempo de espera para las operaciones de lectura y escritura
    instrument.timeout = 10000  # Tiempo de espera de 10 segundos   
    # Configura el delimitador de fin de línea para la comunicación
    instrument.read_termination = '\n'  # Delimitador de fin de línea para lectura
    instrument.write_termination = '\n'  # Delimitador de fin de línea para escritura
    # Limpia el búfer de entrada y salida del instrumento
    instrument.clear()
    # Envía un comando de inicialización al instrumento
    send_command(instrument, '*RST')  # Reinicia el instrumento
    send_command(instrument, '*CLS')  # Limpia el estado del instrumento
    send_command(instrument, '*IDN?')  # Solicita la identificación del instrumento
    idn = instrument.read()  # Lee la identificación del instrumento
    idn = idn.strip()  # Elimina espacios en blanco al inicio y al final
    # Verifica si la identificación contiene la cadena esperada
    print(f'Conectado a: {idn}')  # Imprime la identificación del instrumento


def configure_continuous_capture():
    """
    Configura el instrumento para captura continua.
    """
    global instrument
    send_command(instrument, ':INITiate:CONTinuous ON')  # Activa la captura continua
    send_command(instrument, ':DISPlay:GENeral:MEASview:SELect DPSA')  # Selecciona la vista DPX Spectrum
    send_command(instrument, ':SENSe:DPSA:CLEar:RESults')  # Limpia resultados previos
    send_command(instrument, ':SENSe:DPX:PLOT SPECtrum')  # Configura el modo de espectro
    send_command(instrument, ':SENSe:DPSA:FREQuency:CENTer 1.3E9')  # Frecuencia central
    send_command(instrument, ':SENSe:DPSA:FREQuency:SPAN 40E6')  # Span de frecuencia
    send_command(instrument, ':INPut:ATTenuation 10')  # Atenuación de entrada
    send_command(instrument, ':SENSe:DPSA:BANDwidth:RESolution 1E6')  # Resolución de ancho de banda
    send_command(instrument, ':TRACe3:DPSA:FUNCtion AVERage')  # Configura promedio
    send_command(instrument, ':TRACe3:DPSA:AVERage:COUNt 50')  # Número de promedios
    send_command(instrument, ':TRACe3:DPSA ON')  # Activa la traza 3
    send_command(instrument, ':DISPlay:WAVeform:FORMat DPX')  # Configura el formato de visualización   


def configure_time_overview():
    """
    Configura el instrumento para capturar Time Overview.
    """
    global instrument
    send_command(instrument, ':DISPlay:PULSe:MEASview:NEW TOVerview')  # Selecciona la vista Time Overview
    send_command(instrument, ':INITiate:IMMediate', wait_opc=False)  # Inicia la medición

def capture_and_save_data(fetch_command, process_function, output_file_prefix):
    """
    Captura datos continuamente y los guarda en archivos CSV.
    Args:
        fetch_command (str): Comando SCPI para solicitar los datos.
        process_function (function): Función para procesar los datos capturados.
        output_file_prefix (str): Prefijo para los archivos CSV generados.
    """
    global instrument
    file_index = 1  # Índice para los archivos CSV
    try:
        while True:
            print(f"Capturando datos... Archivo: {output_file_prefix}_{file_index}.csv")
            instrument.write(fetch_command)  # Solicita los datos
            raw_response = instrument.read_raw()  # Lee los datos en formato binario
            try:
                process_function(raw_response, f"{output_file_prefix}_{file_index}.csv")  # Procesa y guarda los datos
                print(f"Datos guardados en '{output_file_prefix}_{file_index}.csv'.")
                file_index += 1
            except Exception as e:
                print(f"Error al procesar los datos: {e}")
            time.sleep(1)  # Espera 1 segundo antes de la siguiente captura
    except KeyboardInterrupt:
        print("Captura continua detenida por el usuario.")



def process_dpx_spectrum(raw_response, output_file):
    """
    Procesa los datos capturados en modo DPX Spectrum y los guarda en un archivo CSV.
    """
    if raw_response[0] == ord('#'):  # Verifica el formato
        num_digits = int(chr(raw_response[1]))
        num_bytes = int(raw_response[2:2 + num_digits].decode())
        header_length = 2 + num_digits
        data_bytes = raw_response[header_length:header_length + num_bytes]
        spectrum_data = struct.unpack(f'<{num_bytes // 4}f', data_bytes)
        spectrum_data = np.array(spectrum_data)
        frequencies = np.linspace(1.3e9 - 20e6, 1.3e9 + 20e6, len(spectrum_data))
        # Guarda los datos en un archivo CSV
        pd.DataFrame({'Frecuencia (Hz)': frequencies, 'Amplitud (dBm)': spectrum_data}).to_csv(output_file, index=False)
    else:
        raise ValueError("Formato de respuesta inesperado en DPX Spectrum.")

def process_time_overview(raw_response, output_file):
    """
    Procesa los datos capturados en modo Time Overview y los guarda en un archivo CSV.
    """
    if raw_response[0] == ord('#'):  # Verifica el formato
        num_digits = int(chr(raw_response[1]))
        num_bytes = int(raw_response[2:2 + num_digits].decode())
        header_length = 2 + num_digits
        data_bytes = raw_response[header_length:header_length + num_bytes]
        time_overview_data = struct.unpack(f'<{num_bytes // 4}f', data_bytes)
        time_overview_data = np.array(time_overview_data)
        # Genera un arreglo de puntos temporales (de 0 a 10 ms)
        time_points = np.linspace(0, 10e-3, len(time_overview_data)) * 1e3  # Convierte a milisegundos
        # Guarda los datos en un archivo CSV
        pd.DataFrame({'Tiempo (ms)': time_points, 'Amplitud (dBm)': time_overview_data}).to_csv(output_file, index=False)
    else:
        raise ValueError("Formato de respuesta inesperado en Time Overview.")

def main():
    """
    Función principal para inicializar, configurar y capturar datos.
    """
    initialize_instrument()
    
    # Configuración y captura en modo DPX Spectrum
    print("\n--- Configurando y capturando DPX Spectrum ---")
    configure_dpx_spectrum()
    capture_and_save_data(':FETCh:DPX:RESults:TRACe3?', process_dpx_spectrum, 'dpx_spectrum')

    # Configuración y captura en modo Time Overview
    print("\n--- Configurando y capturando Time Overview ---")
    configure_time_overview()
    capture_and_save_data(':FETCh:TOVerview?', process_time_overview, 'time_overview')

