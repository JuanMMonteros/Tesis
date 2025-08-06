"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
        
class blk(gr.sync_block):
    def __init__(self, f_start=1e3, f_end=100e3, t_chirp=0.5e-3, prf=1e3, fs=1e6, potencia=1.0):
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
        self.amplitud = np.sqrt(potencia)

        self.N = 2**32
        self.phase_acc = 0
        self.index_chirp = 0

        self.samples_per_chirp = int(self.t_chirp * self.fs)
        self.samples_per_pri = int((1 / self.prf) * self.fs)

        # Precalculamos FTWs del chirp
        self.ftw_array = np.linspace(
            self.f_start * self.N / self.fs,
            self.f_end * self.N / self.fs,
            self.samples_per_chirp
        ).astype(np.uint32)

        # Generamos un buffer de una PRI completa
        self.pri_buffer = np.zeros(self.samples_per_pri, dtype=np.complex64)
        self._generate_pri_buffer()

        self.ptr = 0  # puntero circular

    def _generate_pri_buffer(self):
        phase = 0
        for i in range(self.samples_per_chirp):
            phase = (phase + self.ftw_array[i]) % self.N
            theta = 2 * np.pi * phase / self.N
            self.pri_buffer[i] = self.amplitud * np.exp(1j * theta)

        # Resto del PRI queda en cero (silencio)
        self.pri_buffer[self.samples_per_chirp:] = 0

    def work(self, output_items):
        out = output_items[0]
        noutput = len(out)

        for i in range(noutput):
            out[i] = self.pri_buffer[self.ptr]
            self.ptr = (self.ptr + 1) % len(self.pri_buffer)

        return noutput
        
