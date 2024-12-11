import pandas as pd
import matplotlib.pyplot as plt
import os

# Verzeichnisse für die Daten und Plots
MEASUREMENTS_DIR = os.path.join(os.getcwd(), "measurements")
PLOTS_DIR = os.path.join(os.getcwd(), "plots")

# Sicherstellen, dass der Plots-Ordner existiert
os.makedirs(PLOTS_DIR, exist_ok=True)

# Liste der Algorithmen und zugehörigen Dateinamen
algorithms = ["virtual", "platform", "coroutines", "goroutine"]
csv_files = [os.path.join(MEASUREMENTS_DIR, f"measurement_log_{alg}.csv") for alg in algorithms]

# Der Pfad zur neuen measurement_log_time.csv für Ausführungszeit
TIME_LOG = os.path.join(MEASUREMENTS_DIR, "measurement_log_time.csv")

# Farben für die Plots
colors = ['orange', 'red', 'blue', 'green']  # virtual -> orange, platform -> red, coroutines -> blue, goroutine -> green

# Labels für die Legende
labels = {
    "virtual": "Virtual Threads",
    "platform": "Platform Threads",
    "coroutines": "Coroutinen",
    "goroutine": "Goroutinen"
}

# Maximale und durchschnittliche Werte für jeden Algorithmus speichern
max_values_dict = {}
mean_values_dict = {}

# Daten einlesen und maximalen sowie durchschnittlichen Werte berechnen
for ALGORITHM, csv_file, color in zip(algorithms, csv_files, colors):
    # Daten laden
    data = pd.read_csv(csv_file)

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

# Zusätzliche Daten für Ausführungszeiten einlesen
time_data = pd.read_csv(TIME_LOG)

# Sicherstellen, dass die chunk_number und Ausführungszeit als numerische Werte interpretiert werden
time_data['chunk_number'] = pd.to_numeric(time_data['chunk_number'], errors='coerce')
time_data['virtual'] = pd.to_numeric(time_data['virtual'], errors='coerce')
time_data['platform'] = pd.to_numeric(time_data['platform'], errors='coerce')
time_data['coroutines'] = pd.to_numeric(time_data['coroutines'], errors='coerce')
time_data['goroutines'] = pd.to_numeric(time_data['goroutines'], errors='coerce')

# Funktion für das Plotten
def plot_metric(metric, ylabel, filename, is_threads=False):
    plt.figure(figsize=(10, 5))
    for ALGORITHM, color in zip(algorithms, colors):
        plt.plot(
            max_values_dict[ALGORITHM]['chunk_number'], 
            max_values_dict[ALGORITHM][metric], 
            label=f'{labels[ALGORITHM]} (Max)', 
            marker='^', linestyle='--', color=color
        )
        plt.plot(
            mean_values_dict[ALGORITHM]['chunk_number'], 
            mean_values_dict[ALGORITHM][metric], 
            label=f'{labels[ALGORITHM]} (Mittel)', 
            marker='o', linestyle='-', color=color
        )
    
    plt.title(f'{ylabel} with Max and Mean for Each Chunk Number')
    plt.xlabel('Chunk Number')
    plt.ylabel(ylabel)
    plt.legend(title="Legend", loc="upper left")
    plt.xticks(max_values_dict[algorithms[0]]['chunk_number'])
    plt.grid()
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, filename))
    plt.clf()

# Plot für Ausführungsdauer erstellen (mit den neuen Messungen aus measurement_log_time.csv)
def plot_execution_time():
    plt.figure(figsize=(10, 5))
    plt.plot(time_data['chunk_number'], time_data['virtual'], label='Virtual Threads (Gesamt)', marker='o', linestyle='-', color='orange')
    plt.plot(time_data['chunk_number'], time_data['platform'], label='Platform Threads (Gesamt)', marker='o', linestyle='-', color='red')
    plt.plot(time_data['chunk_number'], time_data['coroutines'], label='Coroutinen (Gesamt)', marker='o', linestyle='-', color='blue')
    plt.plot(time_data['chunk_number'], time_data['goroutines'], label='Goroutinen (Gesamt)', marker='o', linestyle='-', color='green')
    
    plt.title('Ausführungsdauer pro Chunk für verschiedene Algorithmen')
    plt.xlabel('Chunk Number')
    plt.ylabel('Ausführungsdauer (s)')
    plt.legend(title="Legend", loc="upper left")
    plt.xticks(time_data['chunk_number'])
    plt.grid()
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "execution_time_plot.png"))
    plt.clf()

# CPU Usage Plot
plot_metric("cpu_usage", "CPU-Auslastung (%)", "cpu_usage_plot.png")

# Memory Usage Plot
plot_metric("memory_usage", "Arbeitsspeicherverbrauch (MB)", "memory_usage_plot.png")

# Computation Time Plot
plot_execution_time()

# Number of Threads Plot
plot_metric("num_threads", "Thread-Anzahl", "num_threads_plot.png")

print("Plotting done")
