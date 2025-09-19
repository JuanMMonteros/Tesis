#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>
#include <sched.h>
#include <gpiod.h>

#define GPIO_CHIP "/dev/gpiochip0"  // Chip principal
#define GPIO_LINE 21               // GPIO17 (BCM numbering)
#define PERIOD_NS 1000000L          // 2 ms en nanosegundos

static int running = 1;

void handle_sigint(int sig) {
    running = 0;
}

int main() {
    // Afinidad CPU: núcleo 0
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(0, &cpuset);
    if (sched_setaffinity(0, sizeof(cpuset), &cpuset) != 0) {
        perror("sched_setaffinity");
    }

    // Política tiempo real
    struct sched_param param;
    param.sched_priority = 80;
    if (sched_setscheduler(0, SCHED_FIFO, &param) != 0) {
        perror("sched_setscheduler");
    }

    // GPIO
    struct gpiod_chip *chip = gpiod_chip_open(GPIO_CHIP);
    if (!chip) { perror("gpiod_chip_open"); exit(1); }

    struct gpiod_line *line = gpiod_chip_get_line(chip, GPIO_LINE);
    if (!line) { perror("gpiod_chip_get_line"); exit(1); }

    if (gpiod_line_request_output(line, "rt-toggle", 0) < 0) {
        perror("gpiod_line_request_output"); exit(1);
    }

    // Ctrl+C
    signal(SIGINT, handle_sigint);

    struct timespec ts;
    ts.tv_sec = 0;
    ts.tv_nsec = PERIOD_NS;

    int state = 0;

    while (running) {
        state = !state;
        gpiod_line_set_value(line, state);

        // Espera relativa de 2 ms
        if (nanosleep(&ts, NULL) < 0) {
            perror("nanosleep");
        }
    }

    gpiod_line_release(line);
    gpiod_chip_close(chip);

    return 0;
}
