classdef PulseGenerator < handle
    properties
        f_start
        f_end
        t_chirp
        prf
        fs
        potencia
        amplitud
        N
        samples_per_chirp
        samples_per_pri
        ftw_array
        pri_buffer
        nbits
    end
    
    methods
        function obj = PulseGenerator(f_start, f_end, t_chirp, prf, fs, potencia)
            obj.f_start = f_start;
            obj.f_end = f_end;
            obj.t_chirp = t_chirp;
            obj.prf = prf;
            obj.fs = fs;
            obj.potencia = potencia;
            obj.amplitud = sqrt(potencia);
            obj.N = 2^32; % acumulador de fase de 32 bits
            obj.samples_per_chirp = round(obj.t_chirp * obj.fs);
            obj.samples_per_pri = round((1 / obj.prf) * obj.fs);

            % Crear vector de frecuencias lineal en Hz (puede ser negativo)
            freq_array = linspace(obj.f_start, obj.f_end, obj.samples_per_chirp);

            % Convertir a FTW (Frequency Tuning Word) con wrap-around
            obj.ftw_array = mod(round(freq_array * obj.N / obj.fs), obj.N);

            % Generar el primer pulso
            obj.pri_buffer = obj.generate_pulse();
        end
        
        function pulse = generate_pulse(obj)
            phase = 0;
            pulse = zeros(obj.samples_per_pri, 1);

            for i = 1:obj.samples_per_chirp
                % Actualizar acumulador de fase
                phase = mod(phase + obj.ftw_array(i), obj.N);

                % Calcular fase en radianes
                theta = 2 * pi * double(phase) / obj.N;

                % Generar muestra compleja
                pulse(i) = obj.amplitud * exp(1j * theta);
            end
            
            % Rellenar el resto del PRI con silencio
            pulse(obj.samples_per_chirp+1:end) = 0;
        end
        
        function out = next_pulse(obj)
            out = obj.pri_buffer;
        end
    end
end
