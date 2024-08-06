# process_data.py
import pandas as pd
import matplotlib.pyplot as plt

# Datei zum Sammeln aller Messdaten
ALL_DATA = "measurement_log.csv"

# Daten laden
data = pd.read_csv(ALL_DATA)

# Sicherstellen, dass die Daten als numerische Werte interpretiert werden
data['chunk_number'] = pd.to_numeric(data['chunk_number'], errors='coerce')
data['timestamp'] = pd.to_numeric(data['timestamp'], errors='coerce')
data['cpu_usage'] = pd.to_numeric(data['cpu_usage'], errors='coerce')
data['memory_usage'] = pd.to_numeric(data['memory_usage'], errors='coerce')
data['num_threads'] = pd.to_numeric(data['num_threads'], errors='coerce')

# Maximale Werte pro Chunk berechnen
max_values = data.groupby('chunk_number').agg({
    'cpu_usage': 'max',
    'memory_usage': 'max',
}).reset_index()

mean_values = data.groupby('chunk_number').agg({
    'cpu_usage': 'mean',
    'memory_usage': 'mean',
}).reset_index()

grouped = data.groupby('chunk_number')
max_values = grouped.max()
mean_values = grouped.mean()

# Ergebnisse ausgeben
print("Maximale Werte pro Chunk:")
print(max_values)
print(mean_values)

fig, axs = plt.subplots(2, 1, figsize=(10, 8))

# Plot CPU values
axs[0].plot(max_values.index, max_values['cpu_usage'], label='Max CPU', marker='o', linestyle='--', color='r')
axs[0].plot(mean_values.index, mean_values['cpu_usage'], label='Mean CPU', marker='o', linestyle=':', color='b')

axs[0].set_title('CPU Usage with Max and Mean for Each Chunk')
axs[0].set_xlabel('Chunk Number')
axs[0].set_ylabel('CPU Usage')
axs[0].legend()
axs[0].set_xticks(max_values.index)
axs[0].set_xticklabels(max_values.index)

# Plot Memory values
axs[1].plot(max_values.index, max_values['memory_usage'], label='Max RAM', marker='o', linestyle='--', color='r')
axs[1].plot(mean_values.index, mean_values['memory_usage'], label='Mean RAM', marker='o', linestyle=':', color='b')

axs[1].set_title('Memory Usage with Max and Mean for Each Chunk')
axs[1].set_xlabel('Chunk Number')
axs[1].set_ylabel('Memory Usage')
axs[1].legend()
axs[1].set_xticks(max_values.index)
axs[1].set_xticklabels(max_values.index)

plt.tight_layout()
plt.savefig('usage_plot.png')  # Speichern der Plot-Grafik
