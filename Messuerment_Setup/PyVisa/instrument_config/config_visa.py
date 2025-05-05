import pyvisa  # Para comunicación con instrumentos vía VISA
import time  # Para agregar retrasos entre comandos
import csv
import sys

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
    with open(csv_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                # Aplicar delay si está especificado
                if float(row['Delay']) > 0:
                    print(f"Esperando {row['Delay']} segundos...")
                    time.sleep(float(row['Delay']))
                
                if row['Tipo'] == 'Print':
                    print(row['Descripcion'])
                elif row['Tipo'] == 'Comando':
                    param = row['Parametro'] if row['Parametro'] else None
                    send_command(instrument, row['Comando'], param)
                elif row['Tipo'] == 'VerificarError':
                    error_status = instrument.query(row['Comando']).strip()
                    print(f"Estado de error ({row['Descripcion']}): {error_status}")
                elif row['Tipo'] == 'VerificarOPC':
                    opc_response = instrument.query(row['Comando']).strip()
                    print(f"Estado OPC ({row['Descripcion']}): {opc_response}")
                elif row['Tipo'] == 'Espera':
                    continue  # El delay ya se manejó al inicio del ciclo
                
            except Exception as e:
                print(f"Error procesando línea: {row} - {str(e)}")
                # Consultar último error del instrumento
                try:
                    last_error = instrument.query(':SYSTem:ERRor?').strip()
                    print(f"Último error del instrumento: {last_error}")
                except:
                    print("No se pudo obtener último error del instrumento")
                return 1
   
   print("Configuración completada")

   return 0


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
    
    if instrument_config(instrument, 'config.csv')
        for measurement in range(N)
            # Solicitar datos
            
    else:
        instrument.close()

        exit()
