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
            obj.N = 2^32;
            obj.samples_per_chirp = round(obj.t_chirp * obj.fs);
            obj.samples_per_pri = round((1 / obj.prf) * obj.fs);

            % Calcular FTWs
            obj.ftw_array = linspace( ...
                obj.f_start * obj.N / obj.fs, ...
                obj.f_end * obj.N / obj.fs, ...
                obj.samples_per_chirp ...
            );

            obj.pri_buffer = obj.generate_pulse();
        end
        
        function pulse = generate_pulse(obj)
            phase = 0;
            pulse = zeros(obj.samples_per_pri, 1);

            for i = 1:obj.samples_per_chirp
                phase = mod(phase + obj.ftw_array(i), obj.N);
                theta = 2 * pi * phase / obj.N;
                pulse(i) = obj.amplitud * exp(1j * theta);
            end
            
            % Silencio en el resto del PRI
            pulse(obj.samples_per_chirp+1:end) = 0;
        end
        
        function out = next_pulse(obj)
            out = obj.pri_buffer;
        end
    end
end

