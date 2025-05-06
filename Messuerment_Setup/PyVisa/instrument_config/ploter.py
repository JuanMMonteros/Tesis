import pandas as pd
import matplotlib.pyplot as plt

# Leer archivo CSV
archivo_csv = 'dpx_spectrum.csv'  # Cambiá esto si tu archivo tiene otro nombre
df = pd.read_csv(archivo_csv)

# Verificamos que tenga las columnas esperadas
print("Columnas disponibles:", df.columns)

# Ploteamos los datos
plt.figure(figsize=(10, 5))
plt.plot(df['Frecuencia (Hz)'], df['Amplitud (dBm)'], label='Espectro')
plt.xlabel('Frecuencia (Hz)')
plt.ylabel('Amplitud (dBm)')
plt.title('Espectro de Frecuencia')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
