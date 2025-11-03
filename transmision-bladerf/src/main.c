#include <stdlib.h>       // Usada para funciones como malloc, calloc, free, EXIT_FAILURE, etc.
#include <stdbool.h>      // Usada para el tipo `bool`.
#include <stdint.h>       // Usada para tipos como `int8_t`, `int16_t`.
#include <unistd.h>       // Usada para funciones como usleep, sleep.
#include <stdio.h>        // Usada para funciones como printf, fprintf, fopen, fclose.
#include <time.h>         // Usada para nanosleep (pero no se utiliza en el código actual).
#include <libbladeRF.h>   // Usada para la API de BladeRF.
#include <math.h>         // No se utiliza en el código actual.
#include <string.h>       // Usada para funciones como memcpy.
#include "bladerf_config.h" // Usada para configuraciones específicas de BladeRF.
#include "lcd_i2c.h"      // Usada para funciones relacionadas con el LCD.

#if SAMPLE_BITS == 8
typedef int8_t sample_t;
#elif SAMPLE_BITS == 16
typedef int16_t sample_t;
#else
#error "SAMPLE_BITS debe ser 8 o 16"
#endif

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
    display_status("Cargando Waveforms"); 
    usleep(DISPLAY_DELAY);
    
    /*============ Apertura del archivo ============*/
    FILE *f = fopen(CHIRP_FILE, "rb");
    if (!f) {
        display_error("Error: Abrir F", CHIRP_FILE);
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }
    
    /*============ Determinar tamaño del archivo ============*/
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
    
    /*============ Calcular muestras totales y por chirp ============*/
    size_t total_samples = file_size / (2 * sizeof(sample_t));
    if (total_samples % NUM_CHIRPS != 0) {
        display_error("Error: File no divisible", NULL);
        fclose(f);
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }
    
    size_t samples_per_chirp = total_samples / NUM_CHIRPS;
    printf("samples_per_chirp: %zu , total_samples: %zu , WAVEFORM_LEN: %d\n",
           samples_per_chirp, total_samples, WAVEFORM_LEN);
    
    /*============ Asignar memoria para cada waveform ============*/
    sample_t **waveform = calloc(NUM_CHIRPS, sizeof(sample_t *));
    if (!waveform) {
        display_error("Error: Malloc waveform[]", NULL);
        fclose(f);
        bladerf_close(dev);
        close_i2c();
        return EXIT_FAILURE;
    }
    
    /*============ Leer chirps individuales ============*/
    for (int i = 0; i < NUM_CHIRPS; i++) {
        waveform[i] = calloc(WAVEFORM_LEN, sizeof(sample_t));
        if (!waveform[i]) {
            display_error("Error: Malloc waveform[i]", NULL);
            for (int j = 0; j < i; j++) free(waveform[j]);
            free(waveform);
            fclose(f);
            bladerf_close(dev);
            close_i2c();
            return EXIT_FAILURE;
        }
    
        size_t to_read = samples_per_chirp * 2* sizeof(sample_t);
        size_t read = fread(waveform[i], 1, to_read, f);
        if (read != to_read) {
            display_error("Error: Fread chirp", CHIRP_FILE);
            for (int j = 0; j <= i; j++) free(waveform[j]);
            free(waveform);
            fclose(f);
            bladerf_close(dev);
            close_i2c();
            return EXIT_FAILURE;
        }
    
        // Si el chirp es menor que WAVEFORM_LEN, el resto ya está en 0 (calloc)
    }
    
    fclose(f);
    display_status("Waveforms OK");
    usleep(DISPLAY_DELAY);
    
    
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
    int chirp_idx=0; 

    if (TRIGGER_EN) {
        display_status("Esperando Trig...");usleep(DISPLAY_DELAY); 

        while (status == 0) { 
            //Armar trigger para esperar el pulso externo
            status = bladerf_trigger_arm(dev, &trigger, true, 0, 0);

            //Transmitir chirp 
            status = bladerf_sync_tx(dev, waveform[chirp_idx], WAVEFORM_LEN / 2, NULL, 0);
            
            //Actualizar al siguiente chirp
            chirp_idx = (chirp_idx + 1) % NUM_CHIRPS;

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
            status = bladerf_sync_tx(dev, waveform[chirp_idx], WAVEFORM_LEN / 2, NULL, 0);
            if (status != 0) {
                fprintf(stderr, "Error transmitiendo: %s\n", bladerf_strerror(status));
                break;
            }
            chirp_idx = (chirp_idx + 1) % NUM_CHIRPS;
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
