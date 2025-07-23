clear; clc; close all;

%% Parámetros
f_start = 1e3;
f_end = 100e3;
prf = 1e3;
pri = 1/prf;
t_chirp = 0.5*pri;
fs = 2e6;
potencia = 1.0;

%% Instanciar generador discreto
gen = PulseGenerator(f_start, f_end, t_chirp, prf, fs, potencia);
pulse_discreto = gen.next_pulse();

%% Generar por fase directa (analítico)
samples_per_chirp = round(t_chirp * fs);
samples_per_pri = round((1/prf) * fs);
t = (0:samples_per_chirp-1).' / fs;
k = (f_end - f_start) / t_chirp;
theta_direct = 2 * pi * (f_start * t + 0.5 * k .* t.^2);
chirp_direct = sqrt(potencia) * exp(1j * theta_direct);
pulse_directo = [chirp_direct; zeros(samples_per_pri - samples_per_chirp, 1)];

%% Comparación temporal
figure;
subplot(3,1,1);
plot(real(pulse_discreto(1:samples_per_chirp)), '--o');
hold on;
plot(real(pulse_directo(1:samples_per_chirp)));
legend('FTW (discreto)', 'Fase directa');
title('Comparación Temporal - Parte Real');

%% Comparación espectral
NFFT = 1024;
win = hamming(round(NFFT/2));
[Pxx_discreto, f] = pwelch(pulse_discreto, win, [], NFFT, fs, 'centered');
[Pxx_directo, ~] = pwelch(pulse_directo, win, [], NFFT, fs, 'centered');

subplot(3,1,2);
plot(f, 10*log10(Pxx_discreto));
hold on;
plot(f, 10*log10(Pxx_directo), '--');
legend('FTW (discreto)', 'Fase directa');
xlabel('Frecuencia (Hz)');
ylabel('dB');
title('Comparación Espectral');
xlim([-3*f_end 3*f_end])

% Extraer fase
fase_discreto = unwrap(angle(pulse_discreto(1:samples_per_chirp)));
fase_directo = unwrap(angle(pulse_directo(1:samples_per_chirp)));

% Tiempo
t = (0:samples_per_chirp-1).' / fs;

% Graficar comparación de fase
subplot(3,1,3)
plot(t*1e3, fase_discreto, 'b', 'LineWidth', 1.5); hold on;
plot(t*1e3, fase_directo, 'r--', 'LineWidth', 1.5);
xlabel('Tiempo (ms)');
ylabel('Fase (radianes)');
legend('Acumulador FTW', 'Fase directa');
title('Comparación de Fase en el Tiempo');
grid on;
