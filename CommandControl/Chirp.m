clear all
close all
% Parámetros de la señal
f_start = -19e6; % Frecuencia inicial (Hz)
f_end = 19e6;    % Frecuencia final (Hz)
t_chirp = 10e-6; % Duración del chirp (s)
%prf = 1e3;        % Frecuencia de repetición de pulsos (Hz)
fs = 38e6;         % Frecuencia de muestreo (Hz)
potencia = 1.0;   % Potencia de la señal
modo = 'up';      % Modo: 'up' (chirp ascendente) o 'down' (chirp descendente)



% Cálculo de parámetros derivados
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

% Generación del vector de tiempo para el chirp
t = (0:samples_per_chirp-1) / fs;

% Generación de la señal del chirp
k = (f2 - f1) / t_chirp; % Tasa de chirp
y_chirp = amplitud * exp(1j * 2 * pi * (f1 * t + (k/2) * t.^2));


my_signal = zeros(1,2*length(y_chirp));
my_signal(1:samples_per_chirp) = y_chirp;

% Creación del buffer completo del PRI (Periodo de Repetición de Pulso)
%pri_buffer = zeros(1, samples_per_pri);
%pri_buffer(1:samples_per_chirp) = y_chirp;

% Número de pulsos a generar para la visualización
num_pulsos = 5;
sig = repmat(my_signal, 1, num_pulsos);
t_total = (0:length(sig)-1) / fs;


% Ploteo de la señal en el tiempo
figure;
plot(t_total * 1e3, real(sig));
hold on;
plot(t_total * 1e3, imag(sig));
hold off;
title('Señal de pulso con Chirp en el tiempo');
xlabel('Tiempo (ms)');
ylabel('Amplitud');
legend('Parte Real', 'Parte Imaginaria');
grid on;

% Ploteo de la PSD
figure;
pwelch(sig, [], [], [], fs, 'centered');
title('Densidad Espectral de Potencia (PSD)');
xlabel('Frecuencia (Hz)');
ylabel('Potencia/Frecuencia (dB/Hz)');
grid on;



%Saving 100us the signal  in Formato SC16 Q11 bin 

assert(save_sc16q11('Outputs/my_chirp.bin',sig)==1,"La senal debe ser compleja y estat en el rango de 1,-1");

sig_restores = load_sc16q11('Outputs/my_chirp.bin');

assert(sig_restores-sig ==0,"Las dos no son iguales no se esta cargando correctamente elarchivo")

scaleFactor = 2^11;  % Q11 => 11 bits fraccionales
I = real(sig);
Q = imag(sig);

% Escalar y limitar al rango de int16
I_q11 = int16(max(min(I * scaleFactor,  32767), -32768));
Q_q11 = int16(max(min(Q * scaleFactor,  32767), -32768));

% Intercalar I y Q: [I0, Q0, I1, Q1, ...]
IQ_interleaved = zeros(2 * length(I_q11), 1, 'int16');
IQ_interleaved(1:2:end) = I_q11;
IQ_interleaved(2:2:end) = Q_q11;

% -------------------------------------------------------------
% Guardar a archivo binario
% -------------------------------------------------------------
filename = 'chirp_100us_signal_sc16q11.bin';
fid = fopen(filename, 'wb');
fwrite(fid, IQ_interleaved, 'int16');
fclose(fid);

fprintf('Archivo %s guardado en formato SC16 Q11 (%d muestras complejas)\n', ...
        filename, length(I_q11));

