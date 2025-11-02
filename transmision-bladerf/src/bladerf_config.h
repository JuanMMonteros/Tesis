#ifndef BLADERF_CONFIG_H
#define BLADERF_CONFIG_H

#include <libbladeRF.h>

//Ajuste one shot o retardo entre transmisiones
#define DELAY_US 2000  // us
// 1 para habilitar trigger externo, 0 para deshabilitar
#define TRIGGER_EN 0 

// Define para cambiar entre SC8_Q7 (8 bits) y SC16_Q11 (16 bits)
#define SAMPLE_BITS 16
// Archivo con chirp I/Q (pre-generado)
#define CHIRP_FILE "./bin/my_chirpL.bin" 
// Número de chirps en binario
#define NUM_CHIRPS 1

// Define the sample rate for transmission
#define SAMPLE_RATE 38000000 // 38 MHz

// Define the bandwidth
#define BANDWIDTH 50000000 // 50MHz

// Define the center frequency for transmission
#define CENTER_FREQUENCY 1300000000 

// Define the gain for transmission
#define TX_GAIN 40 // Gain in dB

// Define the number of samples to transmit
#define DEVICE_IDENTIFIER "*"

// Parámetros de stream síncrono 
#define TX_NUM_BUFFERS      2
#define TX_SAMPLES_PER_BUF  4096  
#define TX_NUM_XFERS        1
#define STREAM_TIMEOUT_MS   0   

/*==========================================================*/
// Override settings if config_override.h is present
#if __has_include("config_override.h")
    #include "config_override.h"
#endif
/*==========================================================*/

// Longitud total del buffer de transmisión
#define WAVEFORM_LEN (TX_NUM_BUFFERS * TX_SAMPLES_PER_BUF) 

#endif // BLADERF_CONFIG_H