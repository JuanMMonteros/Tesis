#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>
#include <unistd.h>
#include <libbladeRF.h>
#include "bladerf_config.h"   // define DEVICE_IDENTIFIER, SAMPLE_RATE, CENTER_FREQUENCY, TX_GAIN
#include <stdio.h>

/* Parámetros de stream síncrono (ajustables) */
#define TX_NUM_BUFFERS      32
#define TX_SAMPLES_PER_BUF  8192   /* múltiplo de 1024 va bien */
#define TX_NUM_XFERS        8
#define STREAM_TIMEOUT_MS   60000   /* largo si esperás trigger externo */

int main(void)
{
    struct bladerf *dev = NULL;
    int status;

    /* Abrir dispositivo */
    status = bladerf_open(&dev, DEVICE_IDENTIFIER);
    if (status != 0) {
        fprintf(stderr, "Error opening bladeRF device: %s\n", bladerf_strerror(status));
        return EXIT_FAILURE;
    }

    /* Config RF básica */
    unsigned int actual_sr = 0;
    status = bladerf_set_sample_rate(dev, BLADERF_CHANNEL_TX(0), SAMPLE_RATE, &actual_sr);
    if (status != 0) {
        fprintf(stderr, "Error setting sample rate: %s\n", bladerf_strerror(status));
        bladerf_close(dev);
        return EXIT_FAILURE;
    }

    status = bladerf_set_frequency(dev, BLADERF_CHANNEL_TX(0), CENTER_FREQUENCY);
    if (status != 0) {
        fprintf(stderr, "Error setting frequency: %s\n", bladerf_strerror(status));
        bladerf_close(dev);
        return EXIT_FAILURE;
    }

    status = bladerf_set_gain(dev, BLADERF_CHANNEL_TX(0), TX_GAIN);
    if (status != 0) {
        fprintf(stderr, "Error set TX gain: %s\n", bladerf_strerror(status));
        bladerf_close(dev);
        return EXIT_FAILURE;
    }

    /* === Inicializar interfaz síncrona TX === */
    status = bladerf_sync_config(dev,
                                 BLADERF_CHANNEL_TX(0),
                                 BLADERF_FORMAT_SC16_Q11,
                                 TX_NUM_BUFFERS,
                                 TX_SAMPLES_PER_BUF,
                                 TX_NUM_XFERS,
                                 STREAM_TIMEOUT_MS);
    if (status != 0) {
        fprintf(stderr, "sync_config TX: %s\n", bladerf_strerror(status));
        bladerf_close(dev);
        return EXIT_FAILURE;
    }

    /* === Configurar trigger externo (mini_exp[1] = J51-1 en xA4) === */
    struct bladerf_trigger trigger;
    status = bladerf_trigger_init(dev,
                                  BLADERF_CHANNEL_TX(0),
                                  BLADERF_TRIGGER_MINI_EXP_1,
                                  &trigger);
    if (status != 0) {
        fprintf(stderr, "Error inicializando trigger externo: %s\n", bladerf_strerror(status));
        bladerf_close(dev);
        return EXIT_FAILURE;
    }

    /* Rol SLAVE: espera pulso externo */
    trigger.role = BLADERF_TRIGGER_ROLE_SLAVE;

    /* Pre-cargar la forma de onda en memoria */
    FILE *f = fopen("my_chirpL.bin", "rb");
    if (!f) {
        fprintf(stderr, "No se pudo abrir my_chirpL.bin\n");
        bladerf_close(dev);
        return EXIT_FAILURE;
    }

    if (fseek(f, 0, SEEK_END) != 0) {
        fprintf(stderr, "No se pudo determinar el tamaño del archivo\n");
        fclose(f);
        bladerf_close(dev);
        return EXIT_FAILURE;
    }
    long file_size = ftell(f);
    if (file_size <= 0 || file_size % (2 * sizeof(int16_t)) != 0) {
        fprintf(stderr, "Tamaño de archivo inválido\n");
        fclose(f);
        bladerf_close(dev);
        return EXIT_FAILURE;
    }
    rewind(f);

    size_t total_samples = file_size / (2 * sizeof(int16_t));
    int16_t *waveform = malloc(file_size);
    if (!waveform) {
        fprintf(stderr, "No se pudo asignar memoria para la forma de onda\n");
        fclose(f);
        bladerf_close(dev);
        return EXIT_FAILURE;
    }

    size_t read = fread(waveform, 1, file_size, f);
    fclose(f);
    if (read != (size_t)file_size) {
        fprintf(stderr, "Error leyendo my_chirpL.bin\n");
        free(waveform);
        bladerf_close(dev);
        return EXIT_FAILURE;
    }

    /* Habilitar el módulo TX ANTES de transmitir */
    status = bladerf_enable_module(dev, BLADERF_CHANNEL_TX(0), true);
    if (status != 0) {
        fprintf(stderr, "Error enabling TX module: %s\n", bladerf_strerror(status));
        free(waveform);
        bladerf_close(dev);
        return EXIT_FAILURE;
    }

    printf("Esperando trigger externo para transmitir...\n");

    /* Transmisión repetida ante cada disparo */
    const int max_triggers = 1000; /* 0 para infinito */
    int trigger_count = 0;
    while (1) {
        if (max_triggers > 0 && trigger_count >= max_triggers) {
            break;
        }

        status = bladerf_trigger_arm(dev, &trigger, true, 0, 0);
        if (status != 0) {
            fprintf(stderr, "Error armando trigger externo: %s\n", bladerf_strerror(status));
            break;
        }

        bool fired = false;
        status = bladerf_trigger_wait(dev, &trigger, &fired, STREAM_TIMEOUT_MS);
        if (status != 0 || !fired) {
            fprintf(stderr, "Error esperando trigger: %s\n", bladerf_strerror(status));
            bladerf_trigger_arm(dev, &trigger, false, 0, 0);
            break;
        }

        status = bladerf_sync_tx(dev, waveform, total_samples, NULL, STREAM_TIMEOUT_MS);
        if (status != 0) {
            fprintf(stderr, "Error transmitiendo: %s\n", bladerf_strerror(status));
            bladerf_trigger_arm(dev, &trigger, false, 0, 0);
            break;
        }

        status = bladerf_trigger_arm(dev, &trigger, false, 0, 0);
        if (status != 0) {
            fprintf(stderr, "Error desarmando trigger: %s\n", bladerf_strerror(status));
            break;
        }

        trigger_count++;
    }

    printf("Transmisión finalizada.\n");

    /* Limpieza final */
    bladerf_trigger_arm(dev, &trigger, false, 0, 0);
    bladerf_enable_module(dev, BLADERF_CHANNEL_TX(0), false);
    free(waveform);
    bladerf_close(dev);

    return (status == 0) ? EXIT_SUCCESS : EXIT_FAILURE;
}
