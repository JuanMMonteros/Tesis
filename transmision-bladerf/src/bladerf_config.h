#ifndef BLADERF_CONFIG_H
#define BLADERF_CONFIG_H

#include <libbladeRF.h>

// Define the sample rate for transmission
#define SAMPLE_RATE 38000000 // 20 MHz

// Define the center frequency for transmission
#define CENTER_FREQUENCY 1300000000 

// Define the gain for transmission
#define TX_GAIN 10 // Gain in dB

// Define the number of samples to transmit
#define NUM_SAMPLES 1024
#define DEVICE_IDENTIFIER "*"

// Function prototypes
void configure_bladerf(struct bladerf *dev);
void set_tx_gain(struct bladerf *dev, int gain);
void set_sample_rate(struct bladerf *dev, unsigned int rate);
void set_center_frequency(struct bladerf *dev, unsigned int frequency);

#endif // BLADERF_CONFIG_H