#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>
#include <unistd.h>
#include <stdio.h>
#include <sys/time.h>   
#include <libbladeRF.h>       // API bladeRF
#include "bladerf_config.h"   // define configuración bladeRF


static uint64_t now_ms(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint64_t)tv.tv_sec * 1000ULL + (uint64_t)tv.tv_usec / 1000ULL;
}

static int trigger_wait_poll(struct bladerf *dev,
                             struct bladerf_trigger *trig,
                             bool *fired,
                             unsigned timeout_ms)
{
    int status;
    bool is_armed = false, has_fired = false, fire_req = false;
    uint64_t t0 = now_ms();
    *fired = false;

    for (;;) {
        status = bladerf_trigger_state(dev, trig,
                                       &is_armed, &has_fired, &fire_req,
                                       NULL, NULL);
        if (status != 0) return status;

        if (has_fired) { *fired = true; return 0; }
               if (timeout_ms > 0 && (now_ms() - t0) >= timeout_ms) {
            return BLADERF_ERR_TIMEOUT;
        }  
    }
}

int main(void)
{
    struct bladerf *dev = NULL; // Device BladeRF
    int status;                 // Código de estado de funciones bladeRF

    /* Abrir dispositivo */
    status = bladerf_open(&dev, DEVICE_IDENTIFIER);
    if (status != 0) {
        fprintf(stderr, "Error opening bladeRF device: %s\n", bladerf_strerror(status));
        return EXIT_FAILURE;
    }
    /*==========================================================*/
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
    /*==========================================================*/
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

    /*==========================================================*/
    /* Pre-cargar la forma de onda en memoria */
    FILE *f = fopen(CHIRP_FILE, "rb");
    if (!f) {
    fprintf(stderr, "No se pudo abrir %s\n",CHIRP_FILE);
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
        fprintf(stderr, "Error leyendo %s\n",CHIRP_FILE);
        free(waveform);
        bladerf_close(dev);
        return EXIT_FAILURE;
    }

    /*==========================================================*/
    /* Habilitar el módulo TX ANTES de transmitir */
    status = bladerf_enable_module(dev, BLADERF_CHANNEL_TX(0), true);
    if (status != 0) {
        fprintf(stderr, "Error enabling TX module: %s\n", bladerf_strerror(status));
        free(waveform);
        bladerf_close(dev);
        return EXIT_FAILURE;
    }

    printf("Esperando trigger externo para transmitir...\n");
    /*==========================================================*/
    //START LOOP
    /* Transmisión repetida ante cada disparo */
    bool fired = false;
    bool dummy_armed, dummy_fired, dummy_req; //del one shot
    while (1) {
        status = bladerf_trigger_arm(dev, &trigger, true, 0, 0);
        // if (status != 0) {
        //     fprintf(stderr, "Error armando trigger externo: %s\n", bladerf_strerror(status));
        //     break;
        // }

        status = trigger_wait_poll(dev, &trigger, &fired, 0);  // 0 = espera infinita, sin timeout


        // if (status != 0 || !fired) {
        //     fprintf(stderr, "Error esperando trigger: %s\n", bladerf_strerror(status));
        //     bladerf_trigger_arm(dev, &trigger, false, 0, 0);
        //     break;
        // }

        status = bladerf_sync_tx(dev, waveform, total_samples, NULL, 0);
        // if (status != 0) {
        //     fprintf(stderr, "Error transmitiendo: %s\n", bladerf_strerror(status));
        //     bladerf_trigger_arm(dev, &trigger, false, 0, 0);
        //     break;
        // }


        /* === One-shot: esperar a que el pulso del trigger cambie su estado === */
        do {
            bladerf_trigger_state(dev, &trigger,
                                &dummy_armed, &dummy_fired, &dummy_req,
                                NULL, NULL);
            usleep(100);   // espera 2 µs entre consultas
            //printf("Esperando que baje el trigger\n");
        } while (dummy_fired);

        status = bladerf_trigger_arm(dev, &trigger, false, 0, 0);
        // if (status != 0) {
        //     fprintf(stderr, "Error desarmando trigger: %s\n", bladerf_strerror(status));
        //     break;
        // }
        // printf("Transmisión realizada tras trigger\n");
    }
    //END LOOP
    /*==========================================================*/
    //actualmente no sale nunca del loop (agregar condición de salida luego de probar tiempos)
    printf("Transmisión finalizada.\n");

    /* Limpieza final */
    bladerf_trigger_arm(dev, &trigger, false, 0, 0);
    bladerf_enable_module(dev, BLADERF_CHANNEL_TX(0), false);
    free(waveform);
    bladerf_close(dev);

    return (status == 0) ? EXIT_SUCCESS : EXIT_FAILURE;
}
