# Transmision BladeRF

Este proyecto configura una transmisión utilizando la biblioteca libbladerf. A continuación se detallan los archivos y su propósito.

## Estructura del Proyecto

```
transmision-bladerf
├── src
│   ├── main.c                      # Punto de entrada de la aplicación
│   ├── bladerf_config.h            # Configuraciones y definiciones para libbladerf
│   ├── lcd_i2c.c                   # Funciones para LCD
│   ├── lcd_i2c.h                   # Configuraciones y definiciones para LCD
│   └── config_override.h           # Opcional que permite sobrescribir configuraciones
|
├── tools 
│   ├── common_plots.py             # Funciones de post-procesado
│   ├── chirp_generator_phase.py    # genera barridos de fase
│   ├── chirp_generator.py          # Genera chirps unicos y sus config
│   ├── load_chirp.py               # Carga barridos de chirps y plotea
│   ├── concatenator.py             # Concatena binarios
│   └── chirp_generator_phase.py    # genera barridos de fase
|
├── bin                             # Contiene .bin con datos chirp
|
├── obj                             # Contiene .o se crea al compilar
|
├── Makefile                        # Archivo para compilar el proyecto
|
└── README.md                       # Documentación del proyecto
```

## Instrucciones de Compilación

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
## Contribuciones

Las contribuciones son bienvenidas. Si deseas mejorar este proyecto, por favor abre un issue o un pull request.
