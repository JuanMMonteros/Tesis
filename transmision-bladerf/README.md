# ECHO-SIM

El **ECHO-SIM** es un sistema capaz de generar y reproducir múltiples ecos radar simulados utilizando una placa **BladeRF A4 o A9**.  
Permite transmitir formas de onda predefinidas (como chirps o LUTs) de manera sincronizada con un *trigger* externo, emulando ecos reales en un entorno de laboratorio.

---

## Requisitos Previos
- libbladeRF >= 2.4.0  
- GNU Make, gcc  
- Python 3.x (numpy, matplotlib)


## Estructura del Proyecto

```
transmision-bladerf
├── src
│   ├── main.c                      # Punto de entrada de la aplicación (Core sistema)
│   ├── bladerf_config.h            # Configuraciones y definiciones para libbladerf
│   ├── lcd_i2c.c                   # Funciones para LCD
│   ├── lcd_i2c.h                   # Configuraciones y definiciones para LCD
│   └── config_override.h           # Opcional que permite sobrescribir configuraciones
|
├── tools 
│   ├── common_plots.py             # Funciones de post-procesado varias
│   ├── chirp_generator_phase.py    # genera barridos de fase (LUT de chirps)
│   ├── chirp_generator.py          # Genera chirps unicos y sus config
│   ├── concatenator.py             # Concatena binarios
│   └── splitter.py                 # Levanta capturas SARAT, genera binarios individuales y LUT
|
├── bin                             # Contiene .bin con datos chirp
│   └── split_files                 # Contiene binarios individuales generados por splitter.py
|
├── obj                             # Contiene .o se crea al compilar
|
├── Makefile                        # Archivo para compilar el proyecto
|
└── README.md                       # Documentación del proyecto
```

## Instrucciones de Compilación

Es importante antes de correr el programa disponer de los binarios con chirps. Estos ademas se encargaran de proporcionar autogenerados los archivos de configuracion necesarios. Hacer por ejemplo:

```
python3 chirp_generator.py
```

Para compilar el proyecto, asegúrate de tener instalada la biblioteca libbladerf y sus dependencias. Luego, ejecuta el siguiente comando en la terminal desde el directorio raíz del proyecto:

```
make clean
make compile
```

Esto generará el ejecutable en el directorio actual.

## Ejecución de la Aplicación

Una vez compilado, puedes ejecutar la aplicación con el siguiente comando:

```
./nombre_del_ejecutable
```

o con 

```
make run
make run-rt (solo en SO real time)
```
## Make all
Puede realizarce clean compile y run directamente con el comando:

```
make
```
## Configuración de libbladerf

Asegúrate de que el dispositivo BladeRF esté correctamente conectado y configurado. Puedes modificar los parámetros de transmisión en el archivo `src/bladerf_config.h` según tus necesidades. También puedes utilizar `src/config_override.h`, un archivo opcional que permite sobrescribir configuraciones durante la compilación.

## Licencia

Este proyecto se desarrolla en marco de una tesis de grado de la carrera Ingenieria electronica como un comvenio entre UTN y CONAE. Los derechos de propiedad intelectual se encuentran protegidos.

## Información del Proyecto

- **Versión:** 1.0.0
- **Autores:** Joaquín Pappano, Luciano Barberon, Juan Monteros
- **Instituciones:** UTN – CONAE
- **Año:** 2025
