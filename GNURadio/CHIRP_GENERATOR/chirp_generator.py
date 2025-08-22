#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: hola soy la gui
# GNU Radio version: 3.10.9.2

from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import bladeRF
import time
import chirp_generator_epy_block_0 as epy_block_0  # embedded python block




class chirp_generator(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "hola soy la gui", catch_exceptions=True)

        ##################################################
        # Variables
        ##################################################
        self.PRF = PRF = 500
        self.fs = fs = 50e6
        self.PRI = PRI = 1/PRF
        self.samples_for_pulse = samples_for_pulse = fs*PRI
        self.f_start = f_start = -19e6
        self.f_end = f_end = 19e6
        self.T_chirp = T_chirp = 0.5/PRF
        self.P = P = 1

        ##################################################
        # Blocks
        ##################################################

        self.epy_block_0 = epy_block_0.Pulse_generator(f_start=f_start, f_end=f_end, t_chirp=T_chirp, prf=PRF, fs=fs, potencia=P, modo='down')
        self.blocks_add_const_vxx_0 = blocks.add_const_cc(0)
        self.bladeRF_sink_1 = bladeRF.sink(
            args="numchan=" + str(1)
                 + ",metadata=" + 'True'
                 + ",bladerf=" +  str('0')
                 + ",verbosity=" + 'verbose'
                 + ",feature=" + 'default'
                 + ",sample_format=" + '16bit'
                 + ",fpga=" + str('')
                 + ",fpga-reload=" + 'False'
                 + ",use_ref_clk=" + 'True'
                 + ",ref_clk=" + str(int(10e6))
                 + ",buflen=" + str(int(2500))
                 + ",buffers=" + str(int(16))
                 + ",in_clk=" + 'ONBOARD'
                 + ",out_clk=" + str(False)
                 + ",use_dac=" + 'False'
                 + ",dac=" + str(10000)
                 + ",xb200=" + 'none'
                 + ",tamer=" + 'internal'
                 + ",sampling=" + 'internal'
                 + ",lpf_mode="+'disabled'
                 + ",smb="+str(int(0))
                 + ",dc_calibration="+'LPF_TUNING'
                 + ",trigger0="+'False'
                 + ",trigger_role0="+'master'
                 + ",trigger_signal0="+'J51_1'
                 + ",trigger1="+'False'
                 + ",trigger_role1="+'master'
                 + ",trigger_signal1="+'J51_1'
                 + ",bias_tee0="+'False'
                 + ",bias_tee1="+'False'


        )
        self.bladeRF_sink_1.set_sample_rate(fs)
        self.bladeRF_sink_1.set_center_freq(1.3e9,0)
        self.bladeRF_sink_1.set_bandwidth(38e6,0)
        self.bladeRF_sink_1.set_gain(20, 0)
        self.bladeRF_sink_1.set_if_gain(20, 0)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_add_const_vxx_0, 0), (self.bladeRF_sink_1, 0))
        self.connect((self.epy_block_0, 0), (self.blocks_add_const_vxx_0, 0))


    def get_PRF(self):
        return self.PRF

    def set_PRF(self, PRF):
        self.PRF = PRF
        self.set_PRI(1/self.PRF)
        self.set_T_chirp(0.5/self.PRF)
        self.epy_block_0.prf = self.PRF

    def get_fs(self):
        return self.fs

    def set_fs(self, fs):
        self.fs = fs
        self.set_samples_for_pulse(self.fs*self.PRI)
        self.bladeRF_sink_1.set_sample_rate(self.fs)
        self.epy_block_0.fs = self.fs

    def get_PRI(self):
        return self.PRI

    def set_PRI(self, PRI):
        self.PRI = PRI
        self.set_samples_for_pulse(self.fs*self.PRI)

    def get_samples_for_pulse(self):
        return self.samples_for_pulse

    def set_samples_for_pulse(self, samples_for_pulse):
        self.samples_for_pulse = samples_for_pulse

    def get_f_start(self):
        return self.f_start

    def set_f_start(self, f_start):
        self.f_start = f_start
        self.epy_block_0.f_start = self.f_start

    def get_f_end(self):
        return self.f_end

    def set_f_end(self, f_end):
        self.f_end = f_end
        self.epy_block_0.f_end = self.f_end

    def get_T_chirp(self):
        return self.T_chirp

    def set_T_chirp(self, T_chirp):
        self.T_chirp = T_chirp
        self.epy_block_0.t_chirp = self.T_chirp

    def get_P(self):
        return self.P

    def set_P(self, P):
        self.P = P
        self.epy_block_0.potencia = self.P




def main(top_block_cls=chirp_generator, options=None):
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    try:
        input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
