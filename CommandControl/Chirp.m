clear all
close all
f_start = -19e6;
f_end = 19e6;  
t_chirp = 10e-6; 
%prf = 1e3;        
fs = 38e6;         
potencia = 1.0;   
modo = 'up';     



amplitud = sqrt(potencia);
samples_per_chirp = floor(t_chirp * fs);

%samples_per_pri = floor((1 / prf) * fs);

% Invertir frecuencias para modo 'down'
if strcmpi(modo, 'down')
    f1 = f_end;
    f2 = f_start;
else
    f1 = f_start;
    f2 = f_end;
end

% Generacin del vector de tiempo para el chirp
t = (0:samples_per_chirp-1) / fs;

% Generacin de la seal del chirp
k = (f2 - f1) / t_chirp; % Tasa de chirp
y_chirp = amplitud * exp(1j * 2 * pi * (f1 * t + (k/2) * t.^2));


my_signal = zeros(1,2*length(y_chirp));
my_signal(1:samples_per_chirp) = y_chirp;

% Creacin del buffer completo del PRI (Periodo de Repeticin de Pulso)
%pri_buffer = zeros(1, samples_per_pri);
%pri_buffer(1:samples_per_chirp) = y_chirp;

% Nmero de pulsos a generar para la visualizacin
num_pulsos = 1e5*5;
sig = repmat(my_signal, 1, num_pulsos);
t_total = (0:length(sig)-1) / fs;


%Saving 100us the signal  in Formato SC16 Q11 bin 

assert(save_sc16q11('Outputs/my_chirp.bin',sig)==1,"La senal debe ser compleja y estat en el rango de 1,-1");

sig_restores = load_sc16q11('rx_chirp.bin');

Fs   = 38e6;           % Hz
x    = sig_restores(:);% señal compleja en columna
Nfft = 1024;         % 8192 (coincide con tu FFT)
Nw   = 1024;           % tamaño de ventana (p.ej. 4096)
Ovlp = round(0.5*Nw);  % 50% de solapamiento
w    = hann(Nw,"periodic");

% Welch centrado (frecuencia en [-Fs/2, Fs/2])
[PSD, f] = pwelch(x, w, Ovlp, Nfft, Fs, 'centered');   % PSD en W/Hz (si x en voltios)

% En dB/Hz
PSD_dB = 10*log10(PSD + eps);

% Plot
figure;
plot(f/1e6, PSD_dB, 'LineWidth', 1.2); grid on;
xlabel('Frecuencia (MHz)');
ylabel('PSD (dB/Hz)');
title('Densidad Espectral de Potencia - Welch (señal compleja, Fs = 38 MHz)');