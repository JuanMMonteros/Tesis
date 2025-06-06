%% ========================================================================
% Script: An�lisis de estabilidad temporal (PRI/Jitter) en se�ales de radar
% Autores: Juan Monteros/Luciano Barberon/Joaquin Pappano
% Fecha: 25/04/2025
% Descripci�n: 
%   Este script analiza la estabilidad temporal de pulsos en se�ales de radar,
%   calculando el PRI (Pulse Repetition Interval), PRF (Pulse Repetition Frequency),
%   jitter temporal y desviaciones estad�sticas. Incluye visualizaci�n de resultados.
% =========================================================================

%% 1. INICIALIZACI�N DEL ENTORNO
close all;    % Cierra todas las figuras previas
clear all;    % Limpia el workspace
clc;          % Limpia la consola
fprintf('=== AN�LISIS DE ESTABILIDAD TEMPORAL EN SE�ALES DE RADAR ===\n');

%% 2. CARGA Y PREPROCESAMIENTO DE DATOS
nombre_archivo = 'time_overview.csv';  % Archivo con datos tiempo-amplitud

% Verificaci�n de existencia del archivo
if ~isfile(nombre_archivo)
    error('[ERROR] Archivo no encontrado: %s', nombre_archivo);
else
    fprintf('> Leyendo datos de: %s\n', nombre_archivo);
end

% Lectura de datos (ignorando 2 filas de cabecera)
datos = csvread(nombre_archivo, 2, 0);  % Formato: [tiempo(ms), amplitud(dBm)]
t = datos(:, 1) * 1e-3;  % Conversi�n a segundos (si estaba en ms)
V = datos(:, 2);         % Amplitud de la se�al en dBm

%% 3. DETECCI�N DE PULSOS MEDIANTE UMBRALIZACI�N
V_max = max(V);
umbral =sqrt(2)*V_max;  % Umbral de detecci�n (5% sobre el m�ximo)
fprintf('> Umbral de detecci�n: %.2f dBm\n', umbral);

% Algoritmo de detecci�n con supresi�n de rebotes
index_umbral_up = [];
index_umbral_down = [];% �ndices de los pulsos detectados
index_max = [];
i = 1;
while i <= length(V)
    if V(i) > umbral
        % Evita pasarse del largo de V
        window_end = min(i + 100, length(V));  
        [~, idx_local] = max(V(i:window_end));

        index_umbral_up(end+1) = i;  % Registra el �ndice de subida
        index_max(end+1) = i + idx_local - 1;  % �ndice del m�ximo global

        i = window_end;  % Avanza para evitar detecciones m�ltiples

        % Buscar el cruce hacia abajo
        while i <= length(V) && V(i) > umbral
            i = i + 1;
        end

        if i <= length(V)
            index_umbral_down(end+1) = i;
        end
    else
        i = i + 1;
    end
end

% Verificaci�n de pulsos detectados
if isempty(index_umbral_up)
    error('[ERROR] No se detectaron pulsos sobre el umbral');
else
    fprintf('> Pulsos detectados: %d\n', length(index_umbral_up));
end

%% 4. C�LCULO DE PAR�METROS 
% C�lculo de los intervalos entre pulsos (PRI)

t_pulsos = t(index_umbral_up);  % Tiempos de ocurrencia de los pulsos
deltaT = diff(t_pulsos);     % Vector de PRI medidos (en segundos)

% Par�metros te�ricos (ajustar seg�n sistema radar)
PRI_teorico = 1.7241101160313554e-3;  % PRI te�rico en segundos

% C�lculo de jitter temporal
jitter_absoluto = (deltaT - PRI_teorico) * 1e6;  % Jitter en �s
jitter_RMS = std(deltaT) * 1e6;                  % Jitter RMS en �s
max_desviacion = (max(deltaT) - min(deltaT)) * 1e6; % M�xima desviaci�n en �s

% Estad�sticos del PRI
PRI_promedio = mean(deltaT) * 1e6;  % Promedio en �s
varianza_PRI = var(deltaT) * 1e12;  % Varianza en �s�
PRF_medida = 1e6/PRI_promedio;        % PRF en Hz

%% Calculo de Pulse Widht
pw_vector = t(index_umbral_down) - t(index_umbral_up);
pw_mean = mean(pw_vector);
% Figura 1: Se�al temporal con pulsos detectados
dt=t(2)-t(1);
pulse_t= -dt*50:dt:pw_mean+dt*50;
V_prom = cell(1, length(index_umbral_up));
V_means = []; 
V_min = [];
for i = 1:length(index_umbral_up)
    V_prom{i} = V(index_umbral_up(i):index_umbral_down(i));
    V_means(end+1)= mean(10.^((V_prom{i}(25:75)/10)));
    V_min(end+1) = min(V_prom{i}(25:75));
end
V_prom_mw = mean(V_means);
V_min_mw = 10.^(min(V_min)/10);
V_max_mw = 10.^(max(V)/10);
Est_amp=(V_max_mw-V_min_mw)/V_prom_mw*100;

%% 5. VISUALIZACI�N DE RESULTADOS
% ---------------------------------------------------------

% Figura 1: Se�al temporal con pulsos detectados
figure('Name', 'Detecci�n de Pulsos', 'NumberTitle', 'off');
hold on;
for i = 1:length(index_umbral_up)
plot(pulse_t , V(index_umbral_up(i)-50:index_umbral_down(i)+50), '--', 'LineWidth', 1.5);
end
xlim([-dt*50,pw_mean+dt*50])
grid on;
title('Pulse Widh');
xlabel('Tiempo (us)');
ylabel('Amplitud (dBm)');


% Figura 2: Se�al temporal con pulsos detectados
figure('Name', 'Pulse With', 'NumberTitle', 'off');
plot(t()*1e3, V, '-r', 'LineWidth', 1.5);
hold on;
plot(t_pulsos*1e3, V(index_umbral_up), 'bo', 'MarkerSize', 8, 'LineWidth', 1.5);
yline(umbral, '--k', 'Umbral', 'LineWidth', 1.2);
grid on;
title('Se�al de Radar con Pulsos Detectados');
xlabel('Tiempo (ms)');
ylabel('Amplitud (dBm)');
legend('Se�al', 'Pulsos detectados', 'Location', 'best');

% ---------------------------------------------------------
% Figura 3: Histograma de los PRI medidos
figure('Name', 'Distribuci�n del PRI', 'NumberTitle', 'off');
histogram(deltaT*1e6, 20, 'FaceColor', [0.2 0.6 0.8]);
hold on;
xline(PRI_promedio, '--r', 'PRI Promedio', 'LineWidth', 2);
xline(PRI_teorico*1e6, '--g', 'PRI Te�rico', 'LineWidth', 2);
grid on;
title('Distribuci�n del PRI Medido');
xlabel('PRI (�s)');
ylabel('Frecuencia');
legend('Distribuci�n', 'Promedio', 'Te�rico');

% ---------------------------------------------------------
% Figura 4: Evoluci�n temporal del jitter
figure('Name', 'An�lisis de Jitter', 'NumberTitle', 'off');
subplot(2,1,1);
plot(t_pulsos(2:end)*1e3, jitter_absoluto, 'o-', 'LineWidth', 1.5);
grid on;
title('Jitter Absoluto (PRI_{medido} - PRI_{te�rico})');
xlabel('Tiempo (ms)');
ylabel('Jitter (�s)');

subplot(2,1,2);
plot(t_pulsos(2:end)*1e3, deltaT*1e6, 's-', 'LineWidth', 1.5);
grid on;
title('Evoluci�n del PRI Medido');
xlabel('Tiempo (ms)');
ylabel('PRI (�s)');

%% 6. REPORTE DE RESULTADOS
fprintf('\n=== RESULTADOS DEL AN�LISIS ===\n');
fprintf('> PW promedio: %.4f �s\n', pw_mean*1e6);
fprintf('> Estabilidad de Amplitud entre Pulsos: %.4f %%\n', Est_amp);
fprintf('> PRI promedio: %.4f �s\n', PRI_promedio);
fprintf('> Duty Cycle: %.4f%%\n', pw_mean*1e6 / PRI_promedio * 100);
fprintf('> PRF medida: %.2f Hz\n', PRF_medida);
fprintf('> Jitter RMS: %.4f �s\n', jitter_RMS);
fprintf('> M�xima desviaci�n: %.4f �s\n', max_desviacion);
fprintf('> Varianza del PRI: %.4f �s�\n', varianza_PRI);
fprintf('> Error relativo respecto al te�rico: %.6f%%\n', ...
       100*abs(PRI_promedio - PRI_teorico*1e6)/(PRI_teorico*1e6));
