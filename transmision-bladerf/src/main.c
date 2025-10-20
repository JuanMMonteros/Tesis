#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>
#include <unistd.h>
#include <stdio.h>
#include <time.h>         // Para nanosleep
#include <libbladeRF.h>   // API bladeRF
#include <math.h>
#include "bladerf_config.h" // Configuración bladeRF

#if SAMPLE_BITS == 8
typedef int8_t sample_t;
#elif SAMPLE_BITS == 16
typedef int16_t sample_t;
#else
#error "SAMPLE_BITS debe ser 8 o 16"
#endif

// Retardo entre transmisiones en microsegundos
#define DELAY_US 4000  // 500 ms, ajustar según necesidad

void delay_us(unsigned int us)
{
    struct timespec ts;
    ts.tv_sec  = us / 1000000;
    ts.tv_nsec = (us % 1000000) * 1000;
    nanosleep(&ts, NULL);
}

int main(void)
{
    struct bladerf *dev = NULL;
    int status;

    /*===================== Abrir dispositivo =======================*/
    status = bladerf_open(&dev, DEVICE_IDENTIFIER);
    if (status != 0) {
        fprintf(stderr, "Error opening bladeRF device: %s\n", bladerf_strerror(status));
        return EXIT_FAILURE;
    }

    /*======================= Config RF basica ========================*/
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
    
    status = bladerf_set_bandwidth(dev,BLADERF_CHANNEL_TX(0),BANDWIDTH,NULL);
    if (status != 0) {
        fprintf(stderr, "Error setting bandwidth %s\n", bladerf_strerror(status));
        bladerf_close(dev);
        return EXIT_FAILURE;
    }

    status = bladerf_set_gain(dev, BLADERF_CHANNEL_TX(0), TX_GAIN);
    if (status != 0) {
        fprintf(stderr, "Error set TX gain: %s\n", bladerf_strerror(status));
        bladerf_close(dev);
        return EXIT_FAILURE;
    }

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
        fprintf(stderr, "sync_config TX: %s\n", bladerf_strerror(status));
        bladerf_close(dev);
        return EXIT_FAILURE;
    }

    /*============ Pre-cargar la forma de onda en memoria =============*/
    FILE *f = fopen(CHIRP_FILE, "rb");
    if (!f) {
        fprintf(stderr, "No se pudo abrir %s\n", CHIRP_FILE);
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
    if (file_size <= 0 || file_size % (2 * sizeof(sample_t)) != 0) {
        fprintf(stderr, "Tamaño de archivo inválido\n");
        fclose(f);
        bladerf_close(dev);
        return EXIT_FAILURE;
    }
    rewind(f);

    size_t total_samples = file_size / (2 * sizeof(sample_t));
    //sample_t *waveform = malloc(file_size);
    sample_t *waveform = calloc(WAVEFORM_LEN, sizeof(sample_t));
    
    if (!waveform) {
        fprintf(stderr, "No se pudo asignar memoria para la forma de onda\n");
        fclose(f);
        bladerf_close(dev);
        return EXIT_FAILURE;
    }

    size_t read = fread(waveform, 1, file_size, f);
    fclose(f);
    if (read != (size_t)file_size) {
        fprintf(stderr, "Error leyendo %s\n", CHIRP_FILE);
        free(waveform);
        bladerf_close(dev);
        return EXIT_FAILURE;
    }

    /*==== Crear buffer final de tamaño fijo y aplicar ganancia IF ====*/
    
    if (!waveform) {
        fprintf(stderr, "No se pudo asignar memoria para waveform_final\n");
        free(waveform);
        bladerf_close(dev);
        return EXIT_FAILURE;
    }
    
    /*====================== Habilitar módulo TX ======================*/
    status = bladerf_enable_module(dev, BLADERF_CHANNEL_TX(0), true);
    if (status != 0) {
        fprintf(stderr, "Error enabling TX module: %s\n", bladerf_strerror(status));
        free(waveform);
        bladerf_close(dev);
        return EXIT_FAILURE;
    }

    /*==== Configurar trigger externo (mini_exp[1] = J51-1 en xA4) ====*/
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

    // Rol SLAVE: espera pulso externo
    trigger.role = BLADERF_TRIGGER_ROLE_SLAVE;

/*========================= START LOOOP ===========================*/
    /* Transmisión repetida ante cada disparo */
    bool fired = false;
    bool is_armed = false;
    bool fired_req = false;
    printf("Esperando trigger externo para transmitir...\n");

    while (status == 0) { 
        //Armar trigger para esperar el pulso externo
        // status = bladerf_trigger_arm(dev, &trigger, true, 0, 0);

        //Espera activa (polling) del trigger
        do {
            status = bladerf_trigger_state(dev, &trigger,&is_armed, &fired,&fired_req,NULL, NULL);
        } while (!fired);

        //Transmitir chirp 
        status = bladerf_sync_tx(dev, waveform, WAVEFORM_LEN / 2, NULL, 0);

        //One-shot: esperar a que el pulso del trigger cambie su estado
        do {
            bladerf_trigger_state(dev, &trigger,&is_armed, &fired,&fired_req,NULL, NULL);
        } while (fired);

        //Re-armar trigger para la próxima iteración
        // status = bladerf_trigger_arm(dev, &trigger, false, 0, 0);
    }

    if (status != 0) {
        fprintf(stderr, "Error en loop principal: %s\n", bladerf_strerror(status));
        free(waveform);
        bladerf_close(dev);
        return EXIT_FAILURE;
    }
    
    printf("Transmisión finalizada.\n");

    /*========================= Limpieza final ========================*/
    bladerf_enable_module(dev, BLADERF_CHANNEL_TX(0), false);
    free(waveform);
    bladerf_close(dev);

    return (status == 0) ? EXIT_SUCCESS : EXIT_FAILURE;
}