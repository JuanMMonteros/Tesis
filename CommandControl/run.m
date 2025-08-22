% Parámetros
f_start = -19e6;    
f_end = 19e6;    
prf = 508;        
pri = 1/prf;
t_chirp = 0.5*pri; 
fs = 38e6;         
potencia = 1.0;   

% Instanciar generador
gen = PulseGenerator(f_start, f_end, t_chirp, prf, fs, potencia);

% Cantidad de pulsos a generar
N_pulsos = 10;

% Prealocar buffer para almacenar todos los pulsos (opcional)
pulse_length = gen.samples_per_pri;
all_pulses = zeros(pulse_length, N_pulsos);

% Generación de pulsos con while
i = 1;
while i <= N_pulsos
    pulse = gen.next_pulse();
    all_pulses(:, i) = pulse;
    
    fprintf('Pulso %d generado\n', i);
    i = i + 1;
end
assert(save_sc16q11('Outputs/my_chirpL.bin',all_pulses(:,1))==1,"La senal debe ser compleja y estat en el rango de 1,-1");

% Ejemplo: mostrar el primer pulso en dominio temporal
figure(1);
stem(real(all_pulses(:,1)));
ylim([-2 2]);
title('Primer pulso - parte real');

% Ejemplo: visualizar espectro de un pulso
figure(2);
pwelch(all_pulses(:,1), [], [], [], fs, 'centered');
title('Espectro Pulso #1 (frecuencia en Hz)');
xlabel('Frecuencia (Hz)');
