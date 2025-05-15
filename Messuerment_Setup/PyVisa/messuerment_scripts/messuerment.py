# --- Importación de librerías necesarias ---
import pyvisa  # Para comunicación con instrumentos vía VISA (Virtual Instrument Software Architecture)
import numpy as np  # Para operaciones numéricas y manejo de arreglos
import matplotlib.pyplot as plt  # Para graficar los resultados
import struct  # Para desempaquetar datos binarios recibidos del instrumento
import pandas as pd  # Para guardar datos en archivos CSV
import time  # Para agregar retrasos entre comandos
import argparse  #para parsear argumentos
import os        #para crear directorios
import datetime  # Para obtener la fecha y hora actual

# --- Importación de funciones views ---
from config_functions import logger
from config_functions import send_command
from config_functions import DPX
from config_functions import PVT
from config_functions import TimeOverview
from config_functions import Pulse_Trace
from config_functions import Spectrum
from config_functions import frequency
#from pr import Ejemplo_funcion

# --- Lista de views con sus parámetros ---
# Cada view tiene un nombre, estado, número de repeticiones, directorio y función a ejecutar
views = [
    {"name": "DPX", "state": True, "repet": 1,"plot":False,"funtion":DPX,"dir":"dir","executed":1},
    {"name": "PVT", "state": True, "repet": 1,"plot":False,"funtion":PVT,"dir":"dir","executed":1},
    {"name": "TimeOverview", "state": True, "repet": 1,"plot":False,"funtion":TimeOverview,"dir":"dir","executed":1},
    {"name": "Pulse_Trace", "state": True, "repet": 1,"plot":False,"funtion":Pulse_Trace,"dir":"dir","executed":1},
    {"name": "Spectrum", "state": True, "repet": 1,"plot":False,"funtion":Spectrum,"dir":"dir","executed":1},
    {"name": "frequency", "state": True, "repet": 1,"plot":False,"funtion":frequency,"dir":"dir","executed":1},
]


# Crear el parser
parser = argparse.ArgumentParser(description="Mediciones automaticas con PyVISA en Tecktronix RSA6114A")
# Agregar argumentos
parser.add_argument('-ip', type=str, default="192.168.1.67", help="Dirección IP")
parser.add_argument('-dir', type=str, default="results", help="Directorio de resultados")
parser.add_argument('-case', type=str, default="none", help="Ejecutar caso unico Ejemplo: -case DPX")
parser.add_argument('-l', action='store_true', help="Listar los parámetros de ejecución")
parser.add_argument('-w', type=int, default="1", help="delay para cada medicion")
# Parsear los argumentos
args = parser.parse_args()
# Asignar los valores
ip = args.ip
wait = args.w

# --- Configuración inicial de la conexión al instrumento ---
rm = pyvisa.ResourceManager()  # Crea un administrador de recursos para manejar conexiones VISA
instrument = None  # Variable para almacenar la conexión al instrumento (inicialmente None)

# Asignar el directorio de resultados
for view in views:
    view["dir"] = args.dir + "/" + view["name"] #asigna el directorio de resultados


# si se asigna un case solo se ejecuta ese caso una ves 
if(args.case != "none"):
    for view in views:
        if(view["name"]!= args.case):
            view["state"] = False
        view["repet"] = 1



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
        for dir in views:
            if not os.path.exists(dir["dir"]):
                os.makedirs(dir["dir"])
                print(f"Directorio '{dir["dir"]}' creado.")
            else:
                print(f"Directorio '{dir["dir"]}' ya existe.")
        print("_______________________________________________________________\n")

        # --- Bloque principal del script ---
        print("Estableciendo conexión...\n")
        logger("Nueva medición iniciada.\n\n\n")

        # --- Establece conexión con el analizador de espectro Tektronix RSA6114A ---
        instrument = rm.open_resource('TCPIP0::' + ip + '::INSTR')  # Conecta al instrumento vía TCP/IP
        instrument.timeout = 120000  # Establece un timeout largo (120 segundos) para operaciones lentas
        send_command(instrument, '*CLS')  # Limpia el estado del instrumento
        send_command(instrument, '*IDN?', wait_opc=False)  # Solicita la identificación del instrumento
        idn = instrument.read().strip()  # Lee y muestra la identificación (por ejemplo, TEKTRONIX,RSA6114A)
        print(f"Identificación del instrumento: {idn}")
        logger(f"Conexión establecida con instrumento ID:{idn}")
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
                    time.sleep(wait)  # Espera un tiempo
                    logger((f"Medida: {view['name']} - Número: {view['executed'] - 1}"))
                    print(f"Ejecutando mediciones {view['name']}...({view['executed']} de {view['repet']})")
                    view['executed'] += 1
                    repet = True
                    retorno = view["funtion"](instrument, view['dir'], view['plot'])  # llamado a la función

                    logger(f"{retorno}\n_______________________________________________________________") #loggea el retorno de la función
                    print(f"{retorno}\n_______________________________________________________________\n")

except Exception as e: # Captura cualquier excepción que ocurra durante la ejecución
    print("_______________________________________________________________\n")
    print(f"Error general: {e}")
    logger(f"Error general: {e}")
    print("_______________________________________________________________\n")

finally:
    time.sleep(wait)  # Espera un tiempo
    # Cierra la conexión al instrumento y libera recursos
    if instrument is not None:
        instrument.close()  # Cierra la conexión al instrumento
    rm.close()  # Cierra el administrador de recursos
    print("Conexión cerrada correctamente.")
    logger("Conexión cerrada correctamente.\n_______________________________________________________________")
