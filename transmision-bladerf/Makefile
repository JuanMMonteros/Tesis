# Nombre del ejecutable
TARGET = transmision_bladerf

# Directorios
SRC_DIR = src
OBJ_DIR = obj

# Archivos fuente y objeto
SRC = $(SRC_DIR)/main.c
OBJ = $(OBJ_DIR)/main.o

# Compilador y flags
CC = gcc
CFLAGS = -Wall -Wextra -O2
LDFLAGS = -lbladeRF

# Regla por defecto
all: $(TARGET)

# Compilar el ejecutable
$(TARGET): $(OBJ)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Compilar archivo objeto
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	@mkdir -p $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

# ejecuta archivos generados
run:
	./$(TARGET)

# Limpiar archivos generados
clean:
	rm -rf $(OBJ_DIR) $(TARGET)

.PHONY: all clean

