#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>
#include <pthread.h>
#include <sched.h>
#include <gpiod.h>

#define GPIO_CHIP "/dev/gpiochip0"  // Chip principal
#define GPIO_LINE 21                // Pin GPIO17 (BCM)
#define PERIOD_NS 2000000L          // 2 ms en nanosegundos

static int running = 1;

void handle_sigint(int sig) {
    running = 0;
}

int main() {
    // Fijar afinidad a CPU 0
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(0, &cpuset);
    if (sched_setaffinity(0, sizeof(cpuset), &cpuset) != 0) {
        perror("sched_setaffinity");
    }

    // Configurar política en tiempo real
    struct sched_param param;
    param.sched_priority = 80; // prioridad alta (1–99 en SCHED_FIFO)
    if (sched_setscheduler(0, SCHED_FIFO, &param) != 0) {
        perror("sched_setscheduler");
    }

    // Abrir GPIO
    struct gpiod_chip *chip = gpiod_chip_open(GPIO_CHIP);
    if (!chip) { perror("gpiod_chip_open"); exit(1); }

    struct gpiod_line *line = gpiod_chip_get_line(chip, GPIO_LINE);
    if (!line) { perror("gpiod_chip_get_line"); exit(1); }

    if (gpiod_line_request_output(line, "rt-toggle", 0) < 0) {
        perror("gpiod_line_request_output"); exit(1);
    }

    // Capturar Ctrl+C
    signal(SIGINT, handle_sigint);

    // Temporización absoluta
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);

    int state = 0;

    while (running) {
        // Cambiar estado
        state = !state;
        gpiod_line_set_value(line, state);

        // Siguiente instante
        t.tv_nsec += PERIOD_NS;
        while (t.tv_nsec >= 1000000000) {
            t.tv_nsec -= 1000000000;
            t.tv_sec++;
        }
        clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &t, NULL);
    }

    gpiod_line_release(line);
    gpiod_chip_close(chip);

    return 0;
}
