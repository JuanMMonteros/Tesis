# ECHO-SIM

El **ECHO-SIM** es un sistema capaz de generar y reproducir múltiples ecos radar simulados utilizando una placa **BladeRF A4 o A9**.  
Permite transmitir formas de onda predefinidas (como chirps o LUTs) de manera sincronizada con un *trigger* externo, emulando ecos reales en un entorno de laboratorio.

---

## Requisitos Previos
- libbladeRF >= 2.4.0  
- GNU Make, gcc  
- Python 3.x (numpy, matplotlib)

---

## Estructura del Proyecto

```
transmision-bladerf
├── src
│   ├── main.c                      # Punto de entrada de la aplicación (núcleo del sistema)
│   ├── bladerf_config.h            # Configuraciones y definiciones para libbladerf
│   ├── lcd_i2c.c                   # Funciones para el LCD
│   ├── lcd_i2c.h                   # Configuraciones y definiciones para el LCD
│   └── config_override.h           # Opcional: permite sobrescribir configuraciones
|
├── tools 
│   ├── common_plots.py             # Funciones de posprocesado varias
│   ├── chirp_generator_phase.py    # Genera barridos de fase (LUT de chirps)
│   ├── chirp_generator.py          # Genera chirps únicos y sus configuraciones
│   ├── concatenator.py             # Concatena binarios
│   └── splitter.py                 # Procesa capturas SARAT y genera binarios individuales y LUT
|
├── bin                             # Contiene los archivos .bin con datos de chirps
│   └── split_files                 # Contiene binarios individuales generados por splitter.py
|
├── obj                             # Contiene archivos .o, se crea al compilar
|
├── Makefile                        # Archivo para compilar el proyecto
|
└── README.md                       # Documentación del proyecto
```

---

## Instrucciones de Compilación

Antes de ejecutar el programa, es necesario disponer de los binarios con chirps.  
Estos, además, se encargan de generar automáticamente los archivos de configuración necesarios.  
Por ejemplo:

```
python3 chirp_generator.py
```

Para compilar el proyecto, asegúrate de tener instalada la biblioteca **libbladerf** y sus dependencias.  
Luego, ejecuta los siguientes comandos desde el directorio raíz del proyecto:

```
make clean
make compile
```

Esto generará el ejecutable en el directorio actual.

---

## Ejecución de la Aplicación

Una vez compilado, puedes ejecutar la aplicación con el siguiente comando:

```
./nombre_del_ejecutable
```

O bien con:

```
make run
make run-rt   # Solo en sistemas operativos de tiempo real
```

---

## Make all

Puedes realizar *clean*, *compile* y *run* directamente con el comando:

```
make
```

---

## Configuración de libbladerf

Asegúrate de que el dispositivo **BladeRF** esté correctamente conectado y configurado.  
Puedes modificar los parámetros de transmisión en el archivo `src/bladerf_config.h` según tus necesidades.  
También puedes utilizar `src/config_override.h`, un archivo opcional que permite sobrescribir configuraciones durante la compilación.

---

## Licencia

Este proyecto se desarrolla en el marco de una tesis de grado de la carrera de **Ingeniería Electrónica**, como parte de un convenio entre **UTN** y **CONAE**.  
Los derechos de propiedad intelectual se encuentran protegidos.

---

## Información del Proyecto

- **Versión:** 1.0
- **Autores:** Joaquín Pappano, Luciano Barberon, Juan Monteros  
- **Instituciones:** UTN – CONAE  
- **Año:** 2025