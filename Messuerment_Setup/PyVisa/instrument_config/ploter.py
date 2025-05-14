import pandas as pd
import matplotlib.pyplot as plt

# Leer archivo CSV
archivo_csv = 'time_overview.csv'  # Asegúrate de que el archivo esté en el mismo directorio
df = pd.read_csv(archivo_csv)

# Verificar las columnas disponibles
print("Columnas disponibles:", df.columns)

# Configurar el gráfico
plt.figure(figsize=(12, 6))
plt.plot(df['Tiempo (ms)'], df['Amplitud (dBm)'], label='Señal en el tiempo', color='blue', linewidth=1)
plt.xlabel('Tiempo (ms)', fontsize=12)
plt.ylabel('Amplitud (dBm)', fontsize=12)
plt.title('Amplitud vs Tiempo - Chirp de 1.3GHz con 40MHz de ancho de banda', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(fontsize=10)

# Ajustar márgenes y mostrar
plt.tight_layout()
plt.show()
