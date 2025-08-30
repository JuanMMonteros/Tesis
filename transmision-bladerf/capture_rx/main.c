// rx_master_miniexp_capture.c
// Maestro: genera N pulsos en MINI_EXP_1 (PRI=2ms) y captura RX0 exactamente
// (N+2)*PRI*fs muestras en SC16_Q11.
// Compila:  gcc -O2 -Wall -Wextra rx_master_miniexp_capture.c \
//            $(pkg-config --cflags --libs libbladeRF) -lpthread -o rx_master_miniexp_capture
#include <libbladeRF.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <math.h>

/* =================== CONFIG =================== */
#define DEVICE_IDENTIFIER        ""          // "" -> primer dispositivo disponible
#define CENTER_FREQUENCY_HZ      1300e6 // ajustá a tu cadena
#define BANDWIDTH_HZ             38e6  // 2 MHz
#define RX_GAIN_DB               20
#define BUF_SAMPLES              8192        // múltiplo de 1024
#define NUM_BUFFERS              32
#define NUM_TRANSFERS            8
#define STREAM_TIMEOUT_MS        1000
#define PRI_NS                   2000000L    // 2 ms

/* ============ UTILES DE TIEMPO ============ */
static inline void ns_sleep(long ns) {
    struct timespec ts;
    ts.tv_sec  = ns / 1000000000L;
    ts.tv_nsec = ns % 1000000000L;
    nanosleep(&ts, NULL);
}

/* ======== HILO: tren de pulsos en MINI_EXP_1 ========
   Usa la API de triggers como MASTER para la misma señal
   que tu TX esclavo: BLADERF_TRIGGER_MINI_EXP_1. */
struct pulse_args {
    struct bladerf *dev;
    uint32_t num_pulses;
};

static void *pulse_thread(void *arg) {
    struct pulse_args *pa = (struct pulse_args*)arg;

    struct bladerf_trigger trig;
    int st = bladerf_trigger_init(pa->dev,
                                  BLADERF_CHANNEL_TX(0),
                                  BLADERF_TRIGGER_MINI_EXP_1,
                                  &trig);
    if (st != 0) {
        fprintf(stderr, "[MASTER] trigger_init mini_exp_1: %s\n", bladerf_strerror(st));
        return NULL;
    }

    trig.role = BLADERF_TRIGGER_ROLE_MASTER;

    // Armado inicial
    st = bladerf_trigger_arm(pa->dev, &trig, true, 0, 0);
    if (st != 0) {
        fprintf(stderr, "[MASTER] trigger_arm: %s\n", bladerf_strerror(st));
        return NULL;
    }

    // Generar N “fires” con PRI=2 ms
    for (uint32_t k = 0; k < pa->num_pulses; k++) {
        st = bladerf_trigger_fire(pa->dev, &trig);
        if (st != 0) {
            fprintf(stderr, "[MASTER] trigger_fire: %s (k=%u)\n", bladerf_strerror(st), k);
            break;
        }
        ns_sleep(PRI_NS);
    }

    // Desarmar
    (void)bladerf_trigger_arm(pa->dev, &trig, false, 0, 0);
    return NULL;
}

/* ===================== MAIN ===================== */
int main(int argc, char **argv) {
    int status = 0;
    struct bladerf *dev = NULL;
    const char *out_path = "capture_sc16q11.bin";

    // CLI: ./prog [num_pulses] [fs_hz] [out_file]
    uint32_t num_pulses = 10;
    unsigned int fs_hz  = 38e6;

    if (argc >= 2) num_pulses = (uint32_t)strtoul(argv[1], NULL, 10);
    if (argc >= 3) fs_hz      = (unsigned int)strtoul(argv[2], NULL, 10);
    if (argc >= 4) out_path   = argv[3];

    fprintf(stderr, "[MASTER RX] N=%u, PRI=2ms, fs=%u Hz, archivo='%s'\n",
            num_pulses, fs_hz, out_path);

    /* ======= Abrir dispositivo ======= */
    status = bladerf_open(&dev, (strlen(DEVICE_IDENTIFIER) ? DEVICE_IDENTIFIER : NULL));
    if (status != 0) {
        fprintf(stderr, "Error abrir bladeRF: %s\n", bladerf_strerror(status));
        return EXIT_FAILURE;
    }

    /* ======= Config RF + Stream RX0 ======= */
    status = bladerf_set_frequency(dev, BLADERF_CHANNEL_RX(0), (bladerf_frequency)CENTER_FREQUENCY_HZ);
    if (status != 0) { fprintf(stderr, "freq: %s\n", bladerf_strerror(status)); goto cleanup; }

    unsigned int fs_actual = 0;
    status = bladerf_set_sample_rate(dev, BLADERF_CHANNEL_RX(0), fs_hz, &fs_actual);
    if (status != 0) { fprintf(stderr, "samp: %s\n", bladerf_strerror(status)); goto cleanup; }
    if (fs_actual != fs_hz) {
        fprintf(stderr, "Aviso: fs pedida=%u, configurada=%u\n", fs_hz, fs_actual);
        fs_hz = fs_actual;
    }

    status = bladerf_set_bandwidth(dev, BLADERF_CHANNEL_RX(0), (bladerf_bandwidth)BANDWIDTH_HZ, NULL);
    if (status != 0) { fprintf(stderr, "bw: %s\n", bladerf_strerror(status)); goto cleanup; }

    status = bladerf_set_gain(dev, BLADERF_CHANNEL_RX(0), (bladerf_gain)RX_GAIN_DB);
    if (status != 0) { fprintf(stderr, "gain: %s\n", bladerf_strerror(status)); goto cleanup; }

    status = bladerf_sync_config(dev, BLADERF_RX, BLADERF_FORMAT_SC16_Q11,
                                 NUM_BUFFERS, BUF_SAMPLES, NUM_TRANSFERS, STREAM_TIMEOUT_MS);
    if (status != 0) { fprintf(stderr, "sync_config RX: %s\n", bladerf_strerror(status)); goto cleanup; }

    status = bladerf_enable_module(dev, BLADERF_CHANNEL_RX(0), true);
    if (status != 0) { fprintf(stderr, "enable RX: %s\n", bladerf_strerror(status)); goto cleanup; }

    /* ======= Calcular muestras exactas =======
       (N + 2) * PRI * fs  */
    const double pri_s      = (double)PRI_NS / 1e9;     // 0.002 s
    const double dur_total  = (double)(num_pulses + 2u) * pri_s;
    const uint64_t samples_to_capture = (uint64_t) llround(dur_total * (double)fs_hz);

    fprintf(stderr, "[MASTER RX] Capturaré %llu muestras (%.3f s @ %u Hz)\n",
            (unsigned long long)samples_to_capture, dur_total, fs_hz);

    /* ======= Lanzar hilo maestro de pulsos ======= */
    pthread_t th_pulses;
    struct pulse_args pargs = { .dev = dev, .num_pulses = num_pulses };
    if (pthread_create(&th_pulses, NULL, pulse_thread, &pargs) != 0) {
        perror("pthread_create");
        status = -1; goto cleanup;
    }

    /* ======= Captura RX exacta ======= */
    FILE *fout = fopen(out_path, "wb");
    if (!fout) { perror("fopen"); status = -1; pthread_join(th_pulses, NULL); goto cleanup; }

    const size_t elem_per_sample = 2; // I,Q
    int16_t *buf = (int16_t*)malloc(BUF_SAMPLES * elem_per_sample * sizeof(int16_t));
    if (!buf) { fprintf(stderr, "malloc\n"); status = -1; pthread_join(th_pulses, NULL); fclose(fout); goto cleanup; }

    uint64_t captured = 0;
    while (captured < samples_to_capture) {
        size_t to_get = BUF_SAMPLES;
        uint64_t remain = samples_to_capture - captured;
        if (to_get > remain) to_get = (size_t)remain;

        status = bladerf_sync_rx(dev, buf, BUF_SAMPLES, NULL, STREAM_TIMEOUT_MS);
        if (status != 0) {
            if (status == BLADERF_ERR_TIMEOUT) {
                fprintf(stderr, "RX timeout, continuo...\n");
                continue;
            } else {
                fprintf(stderr, "sync_rx: %s\n", bladerf_strerror(status));
                break;
            }
        }

        size_t wrote = fwrite(buf, sizeof(int16_t)*elem_per_sample, to_get, fout);
        if (wrote != to_get) { perror("fwrite"); status = -1; break; }

        captured += to_get;
    }

    pthread_join(th_pulses, NULL);

    fprintf(stderr, "[MASTER RX] Listo. Capturadas %llu / %llu muestras.\n",
            (unsigned long long)captured, (unsigned long long)samples_to_capture);

    free(buf);
    fclose(fout);

cleanup:
    if (dev) {
        bladerf_enable_module(dev, BLADERF_CHANNEL_RX(0), false);
        bladerf_close(dev);
    }
    return (status == 0) ? EXIT_SUCCESS : EXIT_FAILURE;
}
