# Nombre del ejecutable
TARGET = transmision_bladerf

# Directorios
SRC_DIR = src
OBJ_DIR = obj

# Archivos fuente y objeto
SRC = $(SRC_DIR)/main_without_sync.c
OBJ = $(OBJ_DIR)/main.o

# Compilador y flags
CC = gcc
CFLAGS = -Wall -Wextra -O2
LDFLAGS = -lbladeRF -lpthread -lm

# Configuración RT
CPU_CORE = 2        # Núcleo donde se fijará la afinidad
RT_PRIORITY = 95    # Prioridad SCHED_FIFO

# Regla por defecto
all: $(TARGET)

# Compilar el ejecutable
$(TARGET): $(OBJ)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Compilar archivo objeto
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	@mkdir -p $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

# Ejecutar normalmente
run:
	./$(TARGET)

# Ejecutar en tiempo real (SCHED_FIFO + afinidad de CPU)
run-rt: $(TARGET)
	sudo taskset -c $(CPU_CORE) chrt -f $(RT_PRIORITY) ./$(TARGET)

# Limpiar archivos generados
clean:
	rm -rf $(OBJ_DIR) $(TARGET)

.PHONY: all clean run run-rt

