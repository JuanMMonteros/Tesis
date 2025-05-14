# --- Importación de librerías necesarias ---
import pyvisa  # Para comunicación con instrumentos vía VISA (Virtual Instrument Software Architecture)
import numpy as np  # Para operaciones numéricas y manejo de arreglos
#import matplotlib.pyplot as plt  # Para graficar los resultados
import struct  # Para desempaquetar datos binarios recibidos del instrumento
#import pandas as pd  # Para guardar datos en archivos CSV
import time  # Para agregar retrasos entre comandos
import argparse  #para parsear argumentos
import os        #para crear directorios

def Ejemplo_funcion(instr,directorio,plot):
    print(f"Ejecutando funcion... {directorio}")

# Lista de views con sus parámetros
# Cada view tiene un nombre, estado, número de repeticiones, directorio y función a ejecutar
views = [
    {"name": "DPX", "state": True, "repet": 5,"dir":"results/dir1","plot":False,"executed":1,"funtion":Ejemplo_funcion},
    {"name": "TIME", "state": True, "repet": 3,"dir":"results/dir2","plot":False,"executed":1,"funtion":Ejemplo_funcion},
]


# Crear el parser
parser = argparse.ArgumentParser(description="Mediciones automaticas con PyVISA en Tecktronix RSA6114A")
# Agregar argumentos
parser.add_argument('-ip', type=str, default="192.168.1.67", help="Dirección IP")
parser.add_argument('-l', action='store_true', help="Listar los parámetros de ejecución")
# Parsear los argumentos
args = parser.parse_args()
# Asignar los valores
ip = args.ip


# --- Configuración inicial de la conexión al instrumento ---
rm = pyvisa.ResourceManager()  # Crea un administrador de recursos para manejar conexiones VISA
instrument = None  # Variable para almacenar la conexión al instrumento (inicialmente None)


# Comando para el instrumento
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


# Mostrar los valores a ejecutar
print("_______________________________________________________________\n")
print("Mediciones automaticas con PyVISA en Tecktronix RSA6114A")
print("_______________________________________________________________\n")
print("Paramtros script:\n")
print(f"\t -IP: {ip}\n")
for view in views:
    print(f"\t -Mensurement view: {view['name']}")
    print(f"\t\t -Estado: {view['state']}")
    print(f"\t\t -Capturas: {view['repet']}")
    print(f"\t\t -Directorio: {view['dir']}")
    print(f"\t\t -Plot: {view['plot']}\n")
print("_______________________________________________________________\n")

try:
    if not(args.l): #si se usa el flag -l solo se lista los parametros
        # Crear directorios si no existen
        print("Creando directorios...")
        for directory in views:
            if not os.path.exists(directory["dir"]):
                os.makedirs(directory["dir"])
                print(f"Directorio '{directory["dir"]}' creado.")
            else:
                print(f"Directorio '{directory["dir"]}' ya existe.")
        print("_______________________________________________________________\n")

        # --- Bloque principal del script ---
        print("Estableciendo conexión...\n")
        # Establece conexión con el analizador de espectro Tektronix RSA6114A
        instrument = rm.open_resource('TCPIP0::' + ip + '::INSTR')  # Conecta al instrumento vía TCP/IP
        instrument.timeout = 120000  # Establece un timeout largo (120 segundos) para operaciones lentas
        send_command(instrument, '*CLS')  # Limpia el estado del instrumento
        send_command(instrument, '*IDN?', wait_opc=False)  # Solicita la identificación del instrumento
        idn = instrument.read().strip()  # Lee y muestra la identificación (por ejemplo, TEKTRONIX,RSA6114A)
        print(f"Identificación del instrumento: {idn}")
        send_command(instrument, ':INITiate:CONTinuous OFF')  # Desactiva el modo continuo para tomar mediciones únicas
        error_status = instrument.query(':SYSTem:ERRor?').strip()  # Verifica si hay errores después del comando
        print(f"Estado después de :INITiate:CONTinuous OFF: {error_status}")

        print("_______________________________________________________________\n")
        # Ejecutar el bucle de mediciones
        repet = True
        while repet:
            repet = False
            # Ejecutar las mediciones
            for view in views:
                if(view["state"] and view["executed"] <= view["repet"]):
                    print(f"Ejecutando mediciones {view['name']}...({view['executed']} de {view['repet']})")
                    view['executed'] += 1
                    repet = True
                    view["funtion"](instrument,view['dir'],view['plot'])#llamado a la funcion
                    print("_______________________________________________________________\n")

except Exception as e: # Captura cualquier excepción que ocurra durante la ejecución
    print("_______________________________________________________________\n")
    print(f"Error general: {e}")
    print("_______________________________________________________________\n")

finally:
    # Cierra la conexión al instrumento y libera recursos
    if instrument is not None:
        instrument.close()  # Cierra la conexión al instrumento
    rm.close()  # Cierra el administrador de recursos
    print("Conexión cerrada correctamente.")