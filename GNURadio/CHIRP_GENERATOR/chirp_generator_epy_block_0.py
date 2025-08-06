import numpy as np
from gnuradio import gr

class Pulse_generator(gr.sync_block):
    def __init__(self, f_start=-100e3, f_end=100e3, t_chirp=0.5e-3, prf=1e3, fs=1e6, potencia=1.0, modo='up'):
        gr.sync_block.__init__(
            self,
            name='Pulse_generator',   
            in_sig=[],
            out_sig=[np.complex64]
        )
        
        self.f_start = f_start
        self.f_end = f_end
        self.t_chirp = t_chirp
        self.prf = prf
        self.fs = fs
        self.potencia = potencia
        self.modo = modo.lower()
        self.amplitud = np.sqrt(potencia)

        self.N = 2**32  # tamaño del acumulador de fase (32 bits)
        self.samples_per_chirp = int(self.t_chirp * self.fs)
        self.samples_per_pri = int((1 / self.prf) * self.fs)

        # Para modo down invierto f_start y f_end
        if self.modo == 'down':
            f1 = self.f_end
            f2 = self.f_start
        else:
            f1 = self.f_start
            f2 = self.f_end

        # Array de FTW en float64 para soportar valores negativos
        self.ftw_array = np.linspace(
            f1 * self.N / self.fs,
            f2 * self.N / self.fs,
            self.samples_per_chirp
        ).astype(np.float64)

        # Buffer PRI completo
        self.pri_buffer = np.zeros(self.samples_per_pri, dtype=np.complex64)
        self._generate_pri_buffer()

        self.ptr = 0  # puntero circular para salida

    def _generate_pri_buffer(self):
        phase = 0.0
        for i in range(self.samples_per_chirp):
            phase = (phase + self.ftw_array[i]) % self.N
            theta = 2 * np.pi * phase / self.N
            self.pri_buffer[i] = self.amplitud * np.exp(1j * theta)
        # Silencio en el resto del PRI
        self.pri_buffer[self.samples_per_chirp:] = 0

    def work(self, input_items, output_items):
        out = output_items[0]
        noutput = len(out)
        buffer_len = len(self.pri_buffer)

        remaining = buffer_len - self.ptr

        if noutput <= remaining:
            out[:noutput] = self.pri_buffer[self.ptr:self.ptr + noutput]
            self.ptr = (self.ptr + noutput) % buffer_len
        else:
            out[:remaining] = self.pri_buffer[self.ptr:]
            wrap = noutput - remaining
            out[remaining:noutput] = self.pri_buffer[:wrap]
            self.ptr = wrap

        return noutput



        
