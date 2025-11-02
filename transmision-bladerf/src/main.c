#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>
#include <unistd.h>
#include <stdio.h>
#include <time.h>        // Para nanosleep
#include <libbladeRF.h>    // API bladeRF
#include <math.h>
#include <string.h>
#include "bladerf_config.h" // Configuración bladeRF

#if SAMPLE_BITS == 8
typedef int8_t sample_t;
#elif SAMPLE_BITS == 16
typedef int16_t sample_t;
#else
#error "SAMPLE_BITS debe ser 8 o 16"
#endif

/*===========      CONTROLADOR PANTALLA I2C LCD     ==============*/
#include "lcd_i2c.h"
/*================================================================*/

int main(void)
{
    struct bladerf *dev = NULL;
    int status;

    /*===================== Inicializar Display =====================*/
    lcd_start_i2c();
    lcd_init();
    display_status("Iniciando..."); usleep(DISPLAY_DELAY);

    /*===================== Abrir dispositivo =======================*/
    status = bladerf_open(&dev, DEVICE_IDENTIFIER);
    if (status != 0) {
        display_error("Error: OpenDev", bladerf_strerror(status));
        close_i2c(); // Cerrar LCD
        return EXIT_FAILURE;
    }
    display_status("Dev Abierto"); usleep(DISPLAY_DELAY);

    /*======================= Config RF basica ========================*/
    printf("smaple rate : %dMHZ\n",SAMPLE_RATE);
    unsigned int actual_sr = 0;
    status = bladerf_set_sample_rate(dev, BLADERF_CHANNEL_TX(0), SAMPLE_RATE, &actual_sr);
    if (status != 0) {
        display_error("Error: SampRate", bladerf_strerror(status));
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }

    status = bladerf_set_frequency(dev, BLADERF_CHANNEL_TX(0), CENTER_FREQUENCY);
    if (status != 0) {
        display_error("Error: Freq", bladerf_strerror(status));
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }
    
    status = bladerf_set_bandwidth(dev,BLADERF_CHANNEL_TX(0),BANDWIDTH,NULL);
    if (status != 0) {
        display_error("Error: Bandwidth", bladerf_strerror(status));
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }

    status = bladerf_set_gain(dev, BLADERF_CHANNEL_TX(0), TX_GAIN);
    if (status != 0) {
        display_error("Error: TX Gain", bladerf_strerror(status));
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }
    display_status("RF Config OK"); usleep(DISPLAY_DELAY);

    /*================ Inicializar interfaz síncrona TX ===============*/
    bladerf_format format = (SAMPLE_BITS == 8) ? BLADERF_FORMAT_SC8_Q7 : BLADERF_FORMAT_SC16_Q11;

    status = bladerf_sync_config(dev,
                                 BLADERF_CHANNEL_TX(0),
                                 format,
                                 TX_NUM_BUFFERS,
                                 TX_SAMPLES_PER_BUF,
                                 TX_NUM_XFERS,
                                 STREAM_TIMEOUT_MS);
    if (status != 0) {
        display_error("Error: Sync TX", bladerf_strerror(status));
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }

    /*============ Pre-cargar la forma de onda en memoria =============*/
    display_status("Cargando Waveform"); usleep(DISPLAY_DELAY);

    sample_t *waveform = calloc(WAVEFORM_LEN, sizeof(sample_t));  // WAVEFORM_LEN es el tamaño total
    if (!waveform) {
        display_error("Error: Malloc WF", NULL);
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }

    FILE *f = fopen(CHIRP_FILE, "rb");
    if (!f) {
        display_error("Error: Abrir F", CHIRP_FILE);
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }

    /* Ir al final para saber tamaño */
    if (fseek(f, 0, SEEK_END) != 0) {
        display_error("Error: Fseek", NULL);
        fclose(f);
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }

    long file_size = ftell(f);
    if (file_size <= 0 || file_size % (2 * sizeof(sample_t)) != 0) {
        display_error("Error: FileSize", NULL);
        fclose(f);
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }
    rewind(f);

    /* Calcular muestras totales y por chirp */
    size_t total_samples = file_size / (2 * sizeof(sample_t));
    if (total_samples % NUM_CHIRPS != 0) {
        display_error("Error: File no divisible", NULL);
        fclose(f);
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }

    size_t samples_per_chirp = total_samples / NUM_CHIRPS;
    printf("samples_per chirp: %d , total samples: %d , WAVEFORM %d\n", (int)samples_per_chirp, (int)total_samples,WAVEFORM_LEN/2);
    if (samples_per_chirp > WAVEFORM_LEN/2) {
        display_error("Error: Bufer len", NULL);
        fclose(f);
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }

    /* Crear arreglo de punteros */
    sample_t **chirps = calloc(NUM_CHIRPS, sizeof(sample_t *));
    if (!chirps) {
        display_error("Error: Malloc chirps[]", NULL);
        fclose(f);
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }

    /* Leer cada chirp individualmente */
    for (int i = 0; i < NUM_CHIRPS; i++) {
        chirps[i] = calloc(samples_per_chirp, sizeof(sample_t));
        if (!chirps[i]) {
            display_error("Error: Malloc chirp", NULL);
            // liberar todo lo que se haya reservado hasta ahora
            for (int j = 0; j < i; j++) free(chirps[j]);
            free(chirps);
            fclose(f);
            bladerf_close(dev);
            close_i2c();
            return EXIT_FAILURE;
        }

        size_t bytes_to_read = samples_per_chirp * sizeof(sample_t);
        size_t read = fread(chirps[i], 1, bytes_to_read, f);
        if (read != bytes_to_read) {
            display_error("Error: Fread chirp", CHIRP_FILE);
            for (int j = 0; j <= i; j++) free(chirps[j]);
            free(chirps);
            fclose(f);
            bladerf_close(dev);
            close_i2c();
            return EXIT_FAILURE;
        }
    }

    fclose(f);
    display_status("Waveform OK"); usleep(DISPLAY_DELAY);
    
    /*====================== Habilitar módulo TX ======================*/
    status = bladerf_enable_module(dev, BLADERF_CHANNEL_TX(0), true);
    if (status != 0) {
        display_error("Error: Enable TX", bladerf_strerror(status));
        free(waveform);
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }

    /*==== Configurar trigger externo (mini_exp[1] = J51-1 en xA4) ====*/
    struct bladerf_trigger trigger;
    status = bladerf_trigger_init(dev,
                                  BLADERF_CHANNEL_TX(0),
                                  BLADERF_TRIGGER_MINI_EXP_1,
                                  &trigger);
    if (status != 0) {
        display_error("Error: Trig Init", bladerf_strerror(status));
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }

    // Rol SLAVE: espera pulso externo
    trigger.role = BLADERF_TRIGGER_ROLE_SLAVE;

/*========================= START LOOOP ===========================*/
    /* Transmisión repetida ante cada disparo */
    bool fired = false;
    bool is_armed = false;
    bool fired_req = false;
    
    
    // Copiar el chirp completo al inicio del buffer
    memcpy(waveform, chirps[0], samples_per_chirp * 2 * sizeof(sample_t));
    int chirp_idx=0; 

    if (TRIGGER_EN) {
        display_status("Esperando Trig...");usleep(DISPLAY_DELAY); 

        while (status == 0) { 
            //Armar trigger para esperar el pulso externo
            status = bladerf_trigger_arm(dev, &trigger, true, 0, 0);

            //Transmitir chirp 
            status = bladerf_sync_tx(dev, waveform, WAVEFORM_LEN / 2, NULL, 0);
            
            //Actualizar al siguiente chirp
            chirp_idx = (chirp_idx + 1) % NUM_CHIRPS;
            memcpy(waveform, chirps[chirp_idx], samples_per_chirp * 2 * sizeof(sample_t));
            
            //One-shot: esperar a que el pulso del trigger cambie su estado
            usleep(DELAY_US);  // Ajustar según el ancho del pulso de trigger
            do {
                bladerf_trigger_state(dev, &trigger,&is_armed, &fired,&fired_req,NULL, NULL);
            } while (fired && status == 0);
        }

    }else{
        display_status("Transmitiendo..."); 
        /* Loop principal: transmitir repetidamente con retardo */
        while (status == 0) {
            status = bladerf_sync_tx(dev, waveform, WAVEFORM_LEN / 2, NULL, 0);
            if (status != 0) {
                fprintf(stderr, "Error transmitiendo: %s\n", bladerf_strerror(status));
                break;
            }
            chirp_idx = (chirp_idx + 1) % NUM_CHIRPS;
            memcpy(waveform, chirps[chirp_idx], samples_per_chirp * 2 * sizeof(sample_t));
            // Esperar tiempo deseado antes de próxima transmisión
            usleep(DELAY_US);
        }
    }    
        
    if (status != 0) {
        display_error("Error: Main Loop", bladerf_strerror(status));
        free(waveform);
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }
    
    display_status("TX Finalizada");usleep(DISPLAY_DELAY); // Reemplaza a printf

    /*========================= Limpieza final ========================*/
    bladerf_enable_module(dev, BLADERF_CHANNEL_TX(0), false);
    free(waveform);
    bladerf_close(dev);

    // Limpieza del LCD
    display_status("Hecho.");usleep(DISPLAY_DELAY);
    sleep(1);
    lcd_clear();
    close_i2c();

    return (status == 0) ? EXIT_SUCCESS : EXIT_FAILURE;
}
