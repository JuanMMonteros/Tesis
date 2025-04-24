clear all
close all
clc

% Parámetros fundamentales
c = 3e8;              % Velocidad de la luz [m/s]
fC = 5.3e9;           % Frecuencia central [Hz] (banda C)
B = 50e6;             % Ancho de banda [Hz]
tau = 5e-6;           % Duración del pulso [s]
v = 100;              % Velocidad de la plataforma [m/s]

% Tiempos y frecuencias de muestreo
PRF = 1000;           % Frecuencia de repetición de pulsos [Hz]
TS_st = 1/PRF;        % Intervalo de tiempo entre pulsos [s]
TS_ft = 1/(2*B);      % Intervalo de tiempo rápido (fast-time) [s]
nfft = 1024;          % Puntos para la FFT

% Geometría de la escena
x_R_initial = 0;      % Posición inicial del radar [m]
x_f = 500;            % Posición final [m]
y_R = 1000;           % Distancia perpendicular a la trayectoria [m]

% Parámetros de la huella radar
CR_swath_m = 100;     % Ancho mínimo de la huella [m]
CR_swath_M = 150;     % Ancho máximo de la huella [m]

y_m = 800;            % Rango mínimo [m]
y_M = 1200;           % Rango máximo [m]

m = 0.2;              % Pendiente para el cálculo de la huella

% Tiempos para la función echo4
t_i = 0;                      % Tiempo inicial [s]
t_f = 2 * (y_M + CR_swath_M)/c;  % Tiempo final [s] (suficiente para el máximo rango)

% Ruido
N0 = 0;             % Nivel de ruido

% Targets
N = 3; % Numero de targets
targets = [
    % RCS(dBsm)  PosX(m)  PosY(m)
    10,          200,     950;    % Blanco fuerte cerca del centro
    5,           300,     1050;   % Blanco medio
    0,           150,     1100;   % Blanco débil
];

% Inicialización de variables de seguimiento
x_R = x_R_initial;
n = 0;
sigma = [];  % Matriz para almacenar los ecos

while x_R < x_f % x_f posicion final del trayecto
    n = n+1; % Contador de posiciones
    sigma(n,:) = zeros(1,nfft); % Almacena los ecos
    x_R = x_R + v*TS_st; % Actualiza la posicion de acuerdo a la velosidad 
    x(n) = x_R; % Posicion actual
    
    % Antenna footprint 
    % Calcula los límites de la zona iluminada por el radar,
    % limitados por CR_swath_m y CR_swath_M
    
    x_1 = x_R + CR_swath_m/2;
    x_2 = x_R + CR_swath_M/2;
    x_3 = x_R - CR_swath_M/2;
    x_4 = x_R - CR_swath_m/2;
    
    % target range
    for i=1:N 
        % Parametros del target
        sigma_0 = 10^(targets(i,1)/10);
        x_0 = targets(i,2);
        y_0 = targets(i,3);
        
        R = sqrt((x_0-x_R)^2+(y_0-y_R)^2); % Distancia del objetivo
        
        if (((y_0>y_m)&&(y_0<y_M))&&((x_0>x_R-m*y_0)&&(x_0<x_R+m*y_0))) % Si esta dentro del footprint
            sigma(n,:) = sigma_0*echo4(R,TS_ft,t_i,t_f,nfft,B,tau,fC, n, i)+sigma(n,:); % Suma el eco
        end
    end
    
    sigma(n,:) = sigma(n,:) + randn(1,nfft)*N0 + 1j*randn(1,nfft)*N0; % Añade ruido gaussiano complejo
end
%%
% Visualización de la magnitud de los ecos
figure
plot(20*log10(abs(sigma)));
title('Perfil de ecos SAR');
xlabel('Muestras en rango');
ylabel('Posiciones a lo largo de la trayectoria');
colorbar;

figure(3)
% Opción 1: Visualización en escala de grises (magnitud)
subplot(1,2,1);
imagesc(x, 1:nfft, 20*log10(abs(sigma.')));
axis xy;
xlabel('Posición a lo largo de la trayectoria (m)');
ylabel('Muestras en rango');
title('Mapa de ecos (dB)');
colorbar;
colormap('gray');
caxis([max(max(20*log10(abs(sigma.'))))-60 max(max(20*log10(abs(sigma.'))))]); % Ajuste dinámico de 60 dB

% Opción 2: Visualización de la fase
subplot(1,2,2);
imagesc(x, 1:nfft, angle(sigma.'));
axis xy;
xlabel('Posición a lo largo de la trayectoria (m)');
ylabel('Muestras en rango');
title('Fase de los ecos (rad)');
colorbar;
colormap('hsv');

% Ajustes adicionales
set(gcf, 'Position', [100 100 1200 500]); % Tamaño de la figura
sgtitle('Fotograma de la simulación SAR');

function s=echo4(R,TS_ft,t_i,t_f,nfft,B,tau,fC, num, i)
    c=3e8;
    delay_0=(2*R)/c;
    
    % Chirp function synthesis
    t=-tau/2:TS_ft:tau/2;
    K=B/tau;
    s=exp(1j*pi*K*t.^2).*exp(1j*2*pi*fC*delay_0);
    S=fft(s,nfft);
    n=length(t);
    
    if (i == 3) && (num < 2)
        figure(10)
        % Parte real e imaginaria
        subplot(2,1,1);  
        plot(t*1e6, real(s), 'LineWidth', 1.5); hold on;
        plot(t*1e6, imag(s), 'r', 'LineWidth', 1.5);
        xlabel('Tiempo [μs]');
        ylabel('Amplitud');
        title('Parte Real e Imaginaria del Chirp Generado');figure(10)
        % Parte real e imaginaria
        subplot(2,1,1);  
        plot(t*1e6, real(s), 'LineWidth', 1.5); hold on;
        plot(t*1e6, imag(s), 'r', 'LineWidth', 1.5);
        xlabel('Tiempo [μs]');
        ylabel('Amplitud');
        title('Parte Real e Imaginaria del Chirp Generado');
        legend('Real', 'Imaginaria');
        grid on

        % Frecuencia instantánea
        subplot(2,1,2);
        phase = unwrap(angle(s));
        instant_freq = diff(phase)/(2*pi*TS_ft);
        plot(t(1:end-1)*1e6, instant_freq/1e6, 'LineWidth', 1.5);
        xlabel('Tiempo [μs]');
        ylabel('Frecuencia [MHz]');
        title('Frecuencia Instantánea del Chirp');
        grid on;

        sgtitle('Análisis del Chirp LFM en el Dominio del Tiempo');     
    end
    
    % Echo synthesis
    t2=t_i:TS_ft:t_f+2*tau;
    echo=zeros(size(t2));
    i_echo=round((delay_0-t_i)/TS_ft);
    
    if (delay_0)<t_f+2*tau
        echo(1,i_echo)=1;
    end
    
    S2=fft(echo,nfft);
    S=S.*S2;
    s=ifft(S);
    
end

