clear all
close all
clc

% Parámetros fundamentales
c = 3e8;              % Velocidad de la luz [m/s]
fC = 1.3e9;           % Frecuencia central [Hz] (banda L)
lambda = c / fC;      % Longitud de onda [m] (~24 cm)
B = 38e6;             % Ancho de banda [Hz]
v = 200;             % Velocidad de la plataforma [m/s] (Satélite en órbita baja)

tau = 20e-6;           % Duración del pulso [s] (Corto para alta resolución)
PRF = 1200;           % Frecuencia de repetición de pulsos [Hz] (Alta para evitar aliasing)

TS_st = 1/PRF;        % Intervalo de tiempo entre pulsos (slow-time) [s]
fs = 2.5 * B;  % Frecuencia de muestreo (sobremuestreo)

% Geometría de la escena
altura = 10e3;
x_R_initial = 0;      % Posición inicial del radar [m]
x_f = 500;           % Posición final [m]
y_R = altura;           % Distancia perpendicular a la trayectoria [m]

incidencia = 30;               % Ángulo de incidencia [grados]
beta_az = deg2rad(1);          % Ancho del haz en azimut [rad]
beta_r = 10;                        % Ancho del haz en elevación [°]
footprint_az = altura * beta_az * secd(incidencia); % Ancho azimutal [m]
footprint_range = altura * deg2rad(beta_r) / sind(incidencia); % Largo range [m]

% Parámetros de la huella radar (footprint)
swath = footprint_az;         % Ancho de la huella [m] (50 km típico en banda L)
CR_swath_m = swath/2; % Límite inferior de la huella
CR_swath_M = swath;   % Límite superior de la huella

% Rango de distancias (ajustado a ángulo de incidencia)
delta_theta = beta_r/2; % Semi-ancho angular [°]

% Cálculo de los rangos
y_m = altura * tand(incidencia - delta_theta); % Rango mínimo [m]
y_M = altura * tand(incidencia + delta_theta); % Rango máximo [m]

m = tan(beta_az/2);   

nfft_min = ceil((2 * y_M / c) * fs);  
nfft = 2^nextpow2(nfft_min);  % Redondea a potencia de 2
disp(['nfft requerido: ', num2str(nfft)]);

% Tiempos para la función echo4
t_i = 0;                              % Tiempo inicial [s]
t_f = 2 * y_M / c;                    % Tiempo final [s] (para máximo rango)

% Ruido (SNR típico en SAR banda L)
SNR_dB = 20;                          % Relación señal-ruido [dB]
N0 = 10^(-SNR_dB/10);                 % Nivel de ruido normalizado

% Targets
N = 2; % Numero de targets

targets = [
%   dB,  x  ,  y
    10,  400,  6000;   % Target dentro del footprint
    10,  200,  5000;
];

% Inicialización de variables de seguimiento
x_R = x_R_initial;
n = 0;
sigma = [];  % Matriz para almacenar los ecos

% Transmision
[pulso_tx, t_pulso] = generar_pulso_chirp(B, tau, fC, fs);

while x_R < x_f
    n = n + 1;
    
    x_R = x_R + v * TS_st;
    x(n) = x_R;
    sigma(n,:) = zeros(1, nfft);
    
    for i = 1:N
        sigma_0 = 10^(targets(i,1)/10);
        x_0 = targets(i,2);
        y_0 = targets(i,3);
        
        R = sqrt((x_0 - x_R)^2 + (y_0 - y_R)^2);
        
        if ((y_0 > y_m)&&(y_0 < y_M)) && ((x_0 > x_R - m*y_0)&&(x_0 < x_R + m*y_0))
            eco = echo4(R, pulso_tx, fs, nfft, fC);
            sigma(n,:) = sigma(n,:) + sigma_0 * eco;
        end
    end
    
    % Añadir ruido
    sigma(n,:) = sigma(n,:) + randn(1,nfft)*N0 + 1j*randn(1,nfft)*N0;
end

%%
figure(1)
% Umbral en dB para eliminar ecos débiles
umbral_dB = -3;  % Por ejemplo, -3 dB como umbral

for idx = 1:n
    % Convertir la magnitud a dB
    sigma_dB(idx, :) = 20*log10(abs(sigma(idx,:)));
end

sigma(:, abs(sigma_dB) < umbral_dB) = 0;
delta_r = c / (2 * fs);  % Resolución en rango [m]
rango_vector = (0:nfft-1) * delta_r;  % Vector de distancias [m]
h_axis = y_R - rango_vector * cosd(incidencia/2);  % Altura sobre el suelo

subplot(1,2,1);
imagesc(x, h_axis, 20*log10(abs(sigma.')));
axis xy;
xlabel('Posición a lo largo de la trayectoria (m)');
ylabel('Muestras en altura');
title('Mapa de ecos (dB)');
%colorbar;
%colormap('gray');
%caxis([max(max(20*log10(abs(sigma.'))))-60 max(max(20*log10(abs(sigma.'))))]); % Ajuste dinámico de 60 dB

subplot(1,2,2);
imagesc(x, h_axis, angle(sigma.'));
axis xy;
xlabel('Posición a lo largo de la trayectoria (m)');
ylabel('Muestras en altura');
title('Fase de los ecos (rad)');
%colorbar;
%colormap('hsv');

% Ajustes adicionales
set(gcf, 'Position', [100 100 1200 500]); % Tamaño de la figura
sgtitle('Fotograma de la simulación SAR');


%%
function [pulso, t_pulso] = generar_pulso_chirp(B, tau, fC, fs)

    t_pulso = -tau/2 : 1/fs : tau/2 - 1/fs;
    K = B / tau;  % Pendiente del chirp
    pulso = exp(1j*pi*K*t_pulso.^2) .* exp(1j*2*pi*fC*t_pulso);
end

function s = echo4(R, pulso_tx, fs, nfft, fC)
    
    c = 3e8;
    delay_0 = 2*R/c;
    delay_samples = round(delay_0 * fs);
    s = zeros(1, nfft);
    
    if delay_samples + length(pulso_tx) - 1 <= nfft
        s(delay_samples+1 : delay_samples+length(pulso_tx)) = pulso_tx;
        
        % Fase de propagación
        fase = exp(-1j*2*pi*delay_0 * fC);
        s = fase * s;
    else
        warning('Eco fuera del rango del buffer (delay: %.2f muestras)', delay_samples);
    end
end
