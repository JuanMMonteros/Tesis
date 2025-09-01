# Transmision BladeRF

Este proyecto configura una transmisión utilizando la biblioteca libbladerf. A continuación se detallan los archivos y su propósito.

## Estructura del Proyecto

```
transmision-bladerf
├── src
│   ├── main.c            # Punto de entrada de la aplicación
│   ├── bladerf_config.h  # Configuraciones y definiciones para libbladerf
│   └── config_override.h # Opcional que permite sobrescribir configuraciones
├── tools
│   └── common_plots.py   # Funciones de post-procesado
├── bin                   # Contiene .bin con datos chirp
├── obj                   # Contiene .o se crea al compilar
├── Makefile              # Archivo para compilar el proyecto
└── README.md             # Documentación del proyecto
```

## Instrucciones de Compilación

Para compilar el proyecto, asegúrate de tener instalada la biblioteca libbladerf y sus dependencias. Luego, ejecuta el siguiente comando en la terminal desde el directorio raíz del proyecto:

```
make
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
```

Reemplaza `nombre_del_ejecutable` con el nombre que se haya definido en el Makefile. 

## Configuración de libbladerf

Asegúrate de que el dispositivo BladeRF esté correctamente conectado y configurado. Puedes modificar los parámetros de transmisión en el archivo `src/bladerf_config.h` según tus necesidades. También puedes utilizar `src/config_override.h`, un archivo opcional que permite sobrescribir configuraciones durante la compilación.
## Contribuciones

Las contribuciones son bienvenidas. Si deseas mejorar este proyecto, por favor abre un issue o un pull request.
