#ifndef LCD_I2C_H
#define LCD_I2C_H

#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

// Activa o desactiva el uso del LCD a nivel de compilación
#define DISPLAY_EN 1

#if DISPLAY_EN

#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <string.h>

// Retardo para visualización en LCD
#define DISPLAY_DELAY 500000 

// Dirección I2C (0x27 o 0x3F según módulo)
#define I2C_ADDR 0x27

// Bus I2C de Raspberry Pi (normalmente /dev/i2c-1)
#define I2C_BUS "/dev/i2c-1"

// Constantes del LCD
#define LCD_CHR 1        // Enviar datos
#define LCD_CMD 0        // Enviar comando
#define LINEA_1 0x80     // Dirección DDRAM de línea 1
#define LINEA_2 0xC0     // Dirección DDRAM de línea 2
#define LCD_BACKLIGHT 0x08 // Bit para luz de fondo

// Descriptor de archivo del bus I2C
extern int i2c_fd;

// Buffers globales (16 caracteres + null)
extern char lcd_buffer_l1[17];
extern char lcd_buffer_l2[17];

// Prototipos de funciones
void lcd_start_i2c(void);
void lcd_toggle_enable(int bits);
void lcd_send_byte(int bits, int mode);
void lcd_clear(void);
void lcd_display_string(const char *str, int line);
void lcd_init(void);
void display_status(const char *msg);
void display_error(const char *msg, const char *detail);
void close_i2c(void);

#else
// Versiones vacías si DISPLAY_EN = 0
static inline void close_i2c(void) {}
static inline void lcd_start_i2c(void) {}
static inline void lcd_init(void) {}
static inline void lcd_clear(void) {}
static inline void lcd_display_string(const char *str, int line) {
    (void)str;
    (void)line;
}
static inline void display_status(const char *msg) {
    (void)msg;
}
static inline void display_error(const char *msg, const char *detail) {
    (void)msg;
    (void)detail;
}
// Retardo para visualización en LCD
#define DISPLAY_DELAY 0
#endif

#endif // LCD_I2C_H
