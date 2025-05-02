%% ========================================================================
% Script: Análisis de estabilidad temporal (PRI/Jitter) en señales de radar
% Autores: Juan Monteros/Luciano Barberon/Joaquin Pappano
% Fecha: 25/04/2025
% Descripción: 
%   Este script analiza la estabilidad temporal de pulsos en señales de radar,
%   calculando el PRI (Pulse Repetition Interval), PRF (Pulse Repetition Frequency),
%   jitter temporal y desviaciones estadísticas. Incluye visualización de resultados.
% =========================================================================

%% 1. INICIALIZACIÓN DEL ENTORNO
close all;    % Cierra todas las figuras previas
clear all;    % Limpia el workspace
clc;          % Limpia la consola
fprintf('=== ANÁLISIS DE ESTABILIDAD TEMPORAL EN SEÑALES DE RADAR ===\n');

%% 2. CARGA Y PREPROCESAMIENTO DE DATOS
nombre_archivo = 'time_overview.csv';  % Archivo con datos tiempo-amplitud

% Verificación de existencia del archivo
if ~isfile(nombre_archivo)
    error('[ERROR] Archivo no encontrado: %s', nombre_archivo);
else
    fprintf('> Leyendo datos de: %s\n', nombre_archivo);
end

% Lectura de datos (ignorando 2 filas de cabecera)
datos = csvread(nombre_archivo, 2, 0);  % Formato: [tiempo(ms), amplitud(dBm)]
t = datos(:, 1) * 1e-3;  % Conversión a segundos (si estaba en ms)
V = datos(:, 2);         % Amplitud de la señal en dBm

%% 3. DETECCIÓN DE PULSOS MEDIANTE UMBRALIZACIÓN
V_max = max(V);
umbral = 1.05 * V_max;  % Umbral de detección (5% sobre el máximo)
fprintf('> Umbral de detección: %.2f dBm\n', umbral);

% Algoritmo de detección con supresión de rebotes
index_umbral = [];  % Índices de los pulsos detectados
i = 1;
while i <= length(V)
    if V(i) > umbral
        index_umbral(end+1) = i;  % Registra el índice del pulso
        i = i + 100;              % Período de supresión (evita detecciones múltiples)
    else
        i = i + 1;
    end
end

% Verificación de pulsos detectados
if isempty(index_umbral)
    error('[ERROR] No se detectaron pulsos sobre el umbral');
else
    fprintf('> Pulsos detectados: %d\n', length(index_umbral));
end

%% 4. CÁLCULO DE PARÁMETROS TEMPORALES
% Cálculo de los intervalos entre pulsos (PRI)
t_pulsos = t(index_umbral);  % Tiempos de ocurrencia de los pulsos
deltaT = diff(t_pulsos);     % Vector de PRI medidos (en segundos)

% Parámetros teóricos (ajustar según sistema radar)
PRI_teorico = 1.7241101160313554e-3;  % PRI teórico en segundos

% Cálculo de jitter temporal
jitter_absoluto = (deltaT - PRI_teorico) * 1e6;  % Jitter en µs
jitter_RMS = std(deltaT) * 1e6;                  % Jitter RMS en µs
max_desviacion = (max(deltaT) - min(deltaT)) * 1e6; % Máxima desviación en µs

% Estadísticos del PRI
PRI_promedio = mean(deltaT) * 1e6;  % Promedio en µs
varianza_PRI = var(deltaT) * 1e12;  % Varianza en µs²
PRF_medida = 1e6/PRI_promedio;        % PRF en Hz

%% 5. VISUALIZACIÓN DE RESULTADOS
% ---------------------------------------------------------
% Figura 1: Señal temporal con pulsos detectados
figure('Name', 'Detección de Pulsos', 'NumberTitle', 'off');
plot(t*1e3, V, '-r', 'LineWidth', 1.5);
hold on;
plot(t_pulsos*1e3, V(index_umbral), 'bo', 'MarkerSize', 8, 'LineWidth', 1.5);
yline(umbral, '--k', 'Umbral', 'LineWidth', 1.2);
grid on;
title('Señal de Radar con Pulsos Detectados');
xlabel('Tiempo (ms)');
ylabel('Amplitud (dBm)');
legend('Señal', 'Pulsos detectados', 'Location', 'best');

% ---------------------------------------------------------
% Figura 2: Histograma de los PRI medidos
figure('Name', 'Distribución del PRI', 'NumberTitle', 'off');
histogram(deltaT*1e6, 20, 'FaceColor', [0.2 0.6 0.8]);
hold on;
xline(PRI_promedio, '--r', 'PRI Promedio', 'LineWidth', 2);
xline(PRI_teorico*1e6, '--g', 'PRI Teórico', 'LineWidth', 2);
grid on;
title('Distribución del PRI Medido');
xlabel('PRI (µs)');
ylabel('Frecuencia');
legend('Distribución', 'Promedio', 'Teórico');

% ---------------------------------------------------------
% Figura 3: Evolución temporal del jitter
figure('Name', 'Análisis de Jitter', 'NumberTitle', 'off');
subplot(2,1,1);
plot(t_pulsos(2:end)*1e3, jitter_absoluto, 'o-', 'LineWidth', 1.5);
grid on;
title('Jitter Absoluto (PRI_{medido} - PRI_{teórico})');
xlabel('Tiempo (ms)');
ylabel('Jitter (µs)');

subplot(2,1,2);
plot(t_pulsos(2:end)*1e3, deltaT*1e6, 's-', 'LineWidth', 1.5);
grid on;
title('Evolución del PRI Medido');
xlabel('Tiempo (ms)');
ylabel('PRI (µs)');

%% 6. REPORTE DE RESULTADOS
fprintf('\n=== RESULTADOS DEL ANÁLISIS ===\n');
fprintf('> PRI promedio: %.4f µs\n', PRI_promedio);
fprintf('> PRF medida: %.2f Hz\n', PRF_medida);
fprintf('> Jitter RMS: %.4f µs\n', jitter_RMS);
fprintf('> Máxima desviación: %.4f µs\n', max_desviacion);
fprintf('> Varianza del PRI: %.4f µs²\n', varianza_PRI);
%fprintf('> Error relativo respecto al teórico: %.6f%%\n', ...
%       100*abs(PRI_promedio - PRI_teorico*1e6)/PRI_teorico);
