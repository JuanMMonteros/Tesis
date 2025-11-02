#include "lcd_i2c.h"

#if DISPLAY_EN

int i2c_fd;
char lcd_buffer_l1[17];
char lcd_buffer_l2[17];

void lcd_toggle_enable(int bits) {
    usleep(500);
    if (write(i2c_fd, (int[]){bits | 0x04 | LCD_BACKLIGHT}, 1) == -1) {
        perror("Error al escribir en I2C (lcd_toggle_enable - high)");
    }
    usleep(500);
    if (write(i2c_fd, (int[]){(bits & ~0x04) | LCD_BACKLIGHT}, 1) == -1) {
        perror("Error al escribir en I2C (lcd_toggle_enable - low)");
    }
    usleep(500);
}

void lcd_send_byte(int bits, int mode) {
    int bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT;
    int bits_low = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT;

    if (write(i2c_fd, &bits_high, 1) == -1) {
        perror("Error al escribir en I2C (lcd_send_byte - high)");
    }
    lcd_toggle_enable(bits_high);

    if (write(i2c_fd, &bits_low, 1) == -1) {
        perror("Error al escribir en I2C (lcd_send_byte - low)");
    }
    lcd_toggle_enable(bits_low);
}

void lcd_clear(void) {
    lcd_send_byte(0x01, LCD_CMD);
    usleep(5000);
}

void lcd_display_string(const char *str, int line) {
    lcd_send_byte(line, LCD_CMD);
    while (*str) {
        lcd_send_byte(*(str++), LCD_CHR);
    }
}

void lcd_init(void) {
    // Abrir bus I2C
    if ((i2c_fd = open(I2C_BUS, O_RDWR)) < 0) {
        perror("Error al abrir el bus I2C");
        exit(1);
    }

    // Configurar esclavo I2C
    if (ioctl(i2c_fd, I2C_SLAVE, I2C_ADDR) < 0) {
        perror("Error al configurar esclavo I2C");
        exit(1);
    }

    // Inicialización del LCD en modo 4 bits
    lcd_send_byte(0x33, LCD_CMD);
    lcd_send_byte(0x32, LCD_CMD);
    lcd_send_byte(0x06, LCD_CMD);
    lcd_send_byte(0x0C, LCD_CMD);
    lcd_send_byte(0x28, LCD_CMD);
    lcd_send_byte(0x01, LCD_CMD);
    usleep(5000);
}

void display_status(const char *msg) {
    strncpy(lcd_buffer_l1, msg, 16);
    lcd_buffer_l1[16] = '\0';
    lcd_display_string(lcd_buffer_l1, LINEA_1);

    strncpy(lcd_buffer_l2, "                ", 16);
    lcd_buffer_l2[16] = '\0';
    lcd_display_string(lcd_buffer_l2, LINEA_2);
}

void display_error(const char *msg, const char *detail) {
    lcd_clear();
    strncpy(lcd_buffer_l1, msg, 16);
    lcd_buffer_l1[16] = '\0';
    lcd_display_string(lcd_buffer_l1, LINEA_1);

    if (detail) {
        strncpy(lcd_buffer_l2, detail, 16);
        lcd_buffer_l2[16] = '\0';
        lcd_display_string(lcd_buffer_l2, LINEA_2);
    }
}

void lcd_start_i2c(void) {
    if ((i2c_fd = open(I2C_BUS, O_RDWR)) < 0) {
        perror("PANIC: Fallo al abrir el bus I2C");
        exit(EXIT_FAILURE); 
    }
    if (ioctl(i2c_fd, I2C_SLAVE, I2C_ADDR) < 0) {
        perror("PANIC: Fallo al comunicarse con el esclavo");
        close(i2c_fd);
        exit(EXIT_FAILURE);
    }
}

void close_i2c(void) {
    close(i2c_fd);
}


#endif // DISPLAY_EN
