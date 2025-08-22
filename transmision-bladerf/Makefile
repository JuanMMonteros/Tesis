# --- Build config ---
CC       := gcc
CSTD     := -std=c11
WARN     := -Wall -Wextra
CPPFLAGS := -I./src
CFLAGS   := $(CSTD) $(WARN)
LDFLAGS  := -L/usr/local/lib         # ajusta si tu lib no está en /usr/local/lib
LDLIBS   := -lbladeRF                # nombre correcto de la lib

# Usa pkg-config si está disponible (toma rutas y flags correctos)
ifeq ($(shell pkg-config --exists libbladeRF && echo yes),yes)
CPPFLAGS += $(shell pkg-config --cflags libbladeRF)
LDLIBS   := $(shell pkg-config --libs libbladeRF)
# (pkg-config ya incluye -lbladeRF y -L...; puedes comentar LDFLAGS de arriba si quieres)
endif

SRC   := src/main.c
OBJ   := $(SRC:.c=.o)
TARGET:= transmision_bladerf

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS)

%.o: %.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ) $(TARGET)
