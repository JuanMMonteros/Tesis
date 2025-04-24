clear all
close all
clc

% Parámetros fundamentales
c = 3e8;              % Velocidad de la luz [m/s]
fC = 5.3e9;           % Frecuencia central [Hz] (banda C)
B = 50e6;             % Ancho de banda [Hz]
tau = 10e-6;           % Duración del pulso [s]
v = 100;              % Velocidad de la plataforma [m/s]

% Tiempos y frecuencias de muestreo
PRF = 1000;           % Frecuencia de repetición de pulsos [Hz]
TS_st = 1/PRF;        % Intervalo de tiempo entre pulsos [s]
TS_ft = 1/(2*B);      % Intervalo de tiempo rápido (fast-time) [s]
nfft = 1024;          % Puntos para la FFT

% Geometría de la escena
x_R_initial = 0;      % Posición inicial del radar [m]
y_R = 1000;           % Distancia perpendicular a la trayectoria [m]

% Parámetros de la huella radar
CR_swath_m = 100;     % Ancho mínimo de la huella [m]
CR_swath_M = 150;     % Ancho máximo de la huella [m]
y_m = 800;            % Rango mínimo [m]
y_M = 1200;           % Rango máximo [m]

% Tiempos para la función echo4
t_i = 0;                      % Tiempo inicial [s]
t_f = 2 * (y_M + CR_swath_M)/c;  % Tiempo final [s] (suficiente para el máximo rango)

% Ruido
N0 = 0;             % Nivel de ruido

% Inicialización de variables de seguimiento
x_R = x_R_initial;

% Parametros del target
sigma_0 = 1;%10^(targets(i,1)/10);
x_0 = 200;
y_0 = 200;        
R = sqrt((x_0-x_R)^2+(y_0-y_R)^2); % Distancia del objetivo
        
echo4(R,TS_ft,t_i,t_f,nfft,B,tau,fC); % Suma el eco

function s=echo4(R,TS_ft,t_i,t_f,nfft,B,tau,fC)
    c=3e8;
    delay_0=(2*R)/c;
    
    % Chirp function synthesis
    t=-tau/2:TS_ft:tau/2;
    K=B/tau;
    s=exp(1j*pi*K*t.^2).*exp(1j*2*pi*fC*delay_0);
    S=fft(s,nfft);
    n=length(t);
    
    figure(10)
    % Parte real e imaginaria
    subplot(2,1,1);  
    plot(t*1e6, real(s), 'LineWidth', 1.5); 
    hold on;
    plot(t*1e6, imag(s), 'r', 'LineWidth', 1.5);
    xlabel('Tiempo [μs]');
    ylabel('Amplitud');
    title('Parte Real e Imaginaria del Chirp Generado');figure(10)
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