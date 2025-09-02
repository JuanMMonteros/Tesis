#ifndef BLADERF_CONFIG_H
#define BLADERF_CONFIG_H

#include <libbladeRF.h>

// Define para cambiar entre SC8_Q7 (8 bits) y SC16_Q11 (16 bits)
#define SAMPLE_BITS 16

// Archivo con chirp I/Q (pre-generado)
#define CHIRP_FILE "/../bin/my_chirpL.bin" 

// Define the sample rate for transmission
#define SAMPLE_RATE 38000000 // 20 MHz

// Define the center frequency for transmission
#define CENTER_FREQUENCY 1300000000 

// Define the gain for transmission
#define TX_GAIN 10 // Gain in dB

// Define the number of samples to transmit
#define DEVICE_IDENTIFIER "*"

/* Parámetros de stream síncrono (ajustables) */
#define TX_NUM_BUFFERS      2
#define TX_SAMPLES_PER_BUF  1024   /* múltiplo de 1024 va bien */
#define TX_NUM_XFERS        1
#define STREAM_TIMEOUT_MS   0   /* largo si esperás trigger externo */

/*==========================================================*/
// Override settings if config_override.h is present
#if __has_include("config_override.h")
    #include "config_override.h"
#endif
/*==========================================================*/

#endif // BLADERF_CONFIG_H