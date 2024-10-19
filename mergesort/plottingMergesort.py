# process_data.py
import pandas as pd
import matplotlib.pyplot as plt

# Liste der Algorithmen und zugehörigen Dateinamen
algorithms = ["virtual", "platform", "coroutines", "goroutine"]
csv_files = [f"measurement_log_{alg}.csv" for alg in algorithms]

# Farben für die Plots entsprechend deinen Wünschen
colors = ['orange', 'red', 'blue', 'green']  # virtual -> orange, platform -> red, coroutines -> blue, goroutine -> green

# Maximale und durchschnittliche Werte für jeden Algorithmus speichern
max_values_dict = {}
mean_values_dict = {}

# Daten einlesen und maximalen sowie durchschnittlichen Werte berechnen
for ALGORITHM, ALL_DATA, color in zip(algorithms, csv_files, colors):
    # Daten laden
    data = pd.read_csv(ALL_DATA)

    # Sicherstellen, dass die Daten als numerische Werte interpretiert werden
    data['chunk_number'] = pd.to_numeric(data['chunk_number'], errors='coerce')
    data['timestamp'] = pd.to_numeric(data['timestamp'], errors='coerce')
    data['cpu_usage'] = pd.to_numeric(data['cpu_usage'], errors='coerce')
    data['memory_usage'] = pd.to_numeric(data['memory_usage'], errors='coerce')
    data['num_threads'] = pd.to_numeric(data['num_threads'], errors='coerce')

    # Maximale und durchschnittliche Werte pro Chunk berechnen
    max_values = data.groupby('chunk_number').agg({
        'cpu_usage': 'max',
        'memory_usage': 'max',
        'timestamp': 'max',
        'num_threads': 'max',
    }).reset_index()

    mean_values = data.groupby('chunk_number').agg({
        'cpu_usage': 'mean',
        'memory_usage': 'mean',
        'timestamp': 'mean',
        'num_threads': 'mean',
    }).reset_index()

    max_values_dict[ALGORITHM] = max_values
    mean_values_dict[ALGORITHM] = mean_values

# Plot für CPU Usage
plt.figure(figsize=(10, 5))
for ALGORITHM, color in zip(algorithms, colors):
    plt.plot(max_values_dict[ALGORITHM]['chunk_number'], max_values_dict[ALGORITHM]['cpu_usage'], 
             label=f'Max CPU - {ALGORITHM}', marker='^', linestyle='--', color=color)  # Dreieck für max Werte
    plt.plot(mean_values_dict[ALGORITHM]['chunk_number'], mean_values_dict[ALGORITHM]['cpu_usage'], 
             label=f'Mean CPU - {ALGORITHM}', marker='o', linestyle='-', color=color)  # Durchgehende Linie für Mean

plt.title('CPU Usage with Max and Mean for Each Chunk Number')
plt.xlabel('Chunk Number')
plt.ylabel('CPU Usage (%)')
plt.legend()
plt.xticks(max_values_dict[algorithms[0]]['chunk_number'])
plt.grid()
plt.tight_layout()
plt.savefig('cpu_usage_plot_all_algorithms.png')  # Speichern der Plot-Grafik
plt.clf()  # Leere die aktuelle Figur für den nächsten Plot

# Plot für Memory Usage
plt.figure(figsize=(10, 5))
for ALGORITHM, color in zip(algorithms, colors):
    plt.plot(max_values_dict[ALGORITHM]['chunk_number'], max_values_dict[ALGORITHM]['memory_usage'], 
             label=f'Max RAM - {ALGORITHM}', marker='^', linestyle='--', color=color)  # Dreieck für max Werte
    plt.plot(mean_values_dict[ALGORITHM]['chunk_number'], mean_values_dict[ALGORITHM]['memory_usage'], 
             label=f'Mean RAM - {ALGORITHM}', marker='o', linestyle='-', color=color)  # Durchgehende Linie für Mean

plt.title('Memory Usage with Max and Mean for Each Chunk Number')
plt.xlabel('Chunk Number')
plt.ylabel('Memory Usage (MB)')
plt.legend()
plt.xticks(max_values_dict[algorithms[0]]['chunk_number'])
plt.grid()
plt.tight_layout()
plt.savefig('memory_usage_plot_all_algorithms.png')  # Speichern der Plot-Grafik
plt.clf()  # Leere die aktuelle Figur für den nächsten Plot

# Plot für Computation Time
plt.figure(figsize=(10, 5))
for ALGORITHM, color in zip(algorithms, colors):
    plt.plot(max_values_dict[ALGORITHM]['chunk_number'], max_values_dict[ALGORITHM]['timestamp'], 
             label=f'Computation Time - {ALGORITHM}', marker='o', linestyle='-', color=color)  # Dreieck für max Werte

plt.title('Computation Time for Each Chunk Number')
plt.xlabel('Chunk Number')
plt.ylabel('Time (s)')
plt.legend()
plt.xticks(max_values_dict[algorithms[0]]['chunk_number'])
plt.grid()
plt.tight_layout()
plt.savefig('computation_time_plot_all_algorithms.png')  # Speichern der Plot-Grafik
plt.clf()  # Leere die aktuelle Figur für den nächsten Plot

# Plot für Number of Threads
plt.figure(figsize=(10, 5))
for ALGORITHM, color in zip(algorithms, colors):
    plt.plot(max_values_dict[ALGORITHM]['chunk_number'], max_values_dict[ALGORITHM]['num_threads'], 
             label=f'Max Threads - {ALGORITHM}', marker='^', linestyle='--', color=color)  # Dreieck für max Werte
    plt.plot(mean_values_dict[ALGORITHM]['chunk_number'], mean_values_dict[ALGORITHM]['num_threads'], 
             label=f'Mean Threads - {ALGORITHM}', marker='o', linestyle='-', color=color)  # Durchgehende Linie für Mean

plt.title('Number of Threads with Max and Mean for Each Chunk Number')
plt.xlabel('Chunk Number')
plt.ylabel('Thread Number')
plt.legend()
plt.xticks(max_values_dict[algorithms[0]]['chunk_number'])
plt.grid()
plt.tight_layout()
plt.savefig('num_threads_plot_all_algorithms.png')  # Speichern der Plot-Grafik
plt.clf()  # Leere die aktuelle Figur

print("Plotting done")
