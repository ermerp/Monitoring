import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

# Verzeichnisse für die Daten und Plots
MEASUREMENTS_DIR = os.path.join(os.getcwd(), "measurements")
PLOTS_DIR = os.path.join(os.getcwd(), "plots")

# Sicherstellen, dass der Plots-Ordner existiert
os.makedirs(PLOTS_DIR, exist_ok=True)

# Liste der Algorithmen und zugehörigen Dateinamen
algorithms = ["virtual", "platform", "coroutines", "goroutines"]
csv_files = [os.path.join(MEASUREMENTS_DIR, f"measurement_log_{alg}.csv") for alg in algorithms]

# Der Pfad zur neuen measurement_log_time.csv für Ausführungszeit
TIME_LOG = os.path.join(MEASUREMENTS_DIR, "measurement_log_time.csv")

# Farben für die Plots
colors = ['orange', 'red', 'blue', 'green']  # virtual -> orange, platform -> red, coroutines -> blue, goroutines -> green

# Labels für die Legende
labels = {
    "virtual": "Virtual Threads",
    "platform": "Platform Threads",
    "coroutines": "Coroutinen",
    "goroutines": "Goroutinen"
}

# Maximale und durchschnittliche Werte für jeden Algorithmus speichern
max_values_dict = {}
mean_values_dict = {}

# Daten einlesen und maximalen sowie durchschnittlichen Werte berechnen
for ALGORITHM, csv_file, color in zip(algorithms, csv_files, colors):
    data = pd.read_csv(csv_file)
    data['max_depth'] = pd.to_numeric(data['max_depth'], errors='coerce')
    data['cpu_usage'] = pd.to_numeric(data['cpu_usage'], errors='coerce')
    data['memory_usage'] = pd.to_numeric(data['memory_usage'], errors='coerce')
    data['num_threads'] = pd.to_numeric(data['num_threads'], errors='coerce')

    max_values = data.groupby('max_depth').agg({
        'cpu_usage': 'max',
        'memory_usage': 'max',
        'num_threads': 'max',
    }).reset_index()

    mean_values = data.groupby('max_depth').agg({
        'cpu_usage': 'mean',
        'memory_usage': 'mean',
        'num_threads': 'mean',
    }).reset_index()

    max_values_dict[ALGORITHM] = max_values
    mean_values_dict[ALGORITHM] = mean_values

# Zusätzliche Daten für Ausführungszeiten einlesen
time_data = pd.read_csv(TIME_LOG)
time_data['max_depth'] = pd.to_numeric(time_data['max_depth'], errors='coerce')
time_data['virtual'] = pd.to_numeric(time_data['virtual'], errors='coerce')
time_data['platform'] = pd.to_numeric(time_data['platform'], errors='coerce')
time_data['coroutines'] = pd.to_numeric(time_data['coroutines'], errors='coerce')
time_data['goroutines'] = pd.to_numeric(time_data['goroutines'], errors='coerce')

# Funktion für das Plotten von Metriken als Säulendiagramm
def plot_metric_bar(metric, ylabel, filename):
    plt.figure(figsize=(12, 6))
    
    width = 0.2  # Breite der Balken
    num_algorithms = len(algorithms)
    
    for i, (ALGORITHM, color) in enumerate(zip(algorithms, colors)):
        max_values = max_values_dict[ALGORITHM]
        mean_values = mean_values_dict[ALGORITHM]
        
        # Positionen auf der X-Achse für die Balken
        positions = max_values['max_depth'] + (i - (num_algorithms - 1) / 2) * width
        
        # Max-Wert-Balken
        plt.bar(
            positions,
            max_values[metric],  # Höhe der Balken
            width=width,
            label=f'{labels[ALGORITHM]} (Max)',
            color=color,
            alpha=0.4
        )

        # Mittelwert-Balken
        plt.bar(
            positions,
            mean_values[metric],  # Höhe der Balken
            width=width,
            label=f'{labels[ALGORITHM]} (Mittel)',
            color=color,
            alpha=1.0
        )

    plt.title(f'{ylabel} mit Maximal- und Mittelwerten pro maximaler Baumebene')
    plt.xlabel('Maximale Baumebene')
    plt.ylabel(ylabel)

    # Anpassung der Legende
    plt.legend(
        title="Legende", 
        loc="upper center", 
        bbox_to_anchor=(0.5, -0.2),
        ncol=4,
        columnspacing=1,
        handlelength=2
    )
    
    plt.xticks(max_values_dict[algorithms[0]]['max_depth'])
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, filename))
    plt.clf()


# Plot für Ausführungsdauer als Säulendiagramm erstellen
def plot_execution_time_bar():
    plt.figure(figsize=(12, 6))
    
    width = 0.2  # Breite der Balken
    num_algorithms = len(algorithms)
    
    for i, (ALGORITHM, color) in enumerate(zip(algorithms, colors)):
        # Positionen auf der X-Achse für die Balken
        positions = time_data['max_depth'] + (i - (num_algorithms - 1) / 2) * width
        
        # Zeichne die Balken
        plt.bar(
            positions,
            time_data[ALGORITHM],  # Höhe der Balken
            width=width,
            label=labels[ALGORITHM],
            color=color,
            alpha=0.7
        )

    plt.title('Ausführungsdauer pro maximaler Baumebene')
    plt.xlabel('Maximale Baumebene')  # X-Achse als Baum-Ebene bezeichnen
    plt.ylabel('Ausführungsdauer (s)')

    # Positioniere die Legende unter dem Diagramm
    plt.legend(
        title="Legende", 
        loc="upper center", 
        bbox_to_anchor=(0.5, -0.2),  # Legende unter dem Diagramm positionieren
        ncol=4,  # Anzahl der Spalten in der Legende
        columnspacing=1,  # Abstand zwischen den Spalten in der Legende
        handlelength=2  # Länge der Symbole in der Legende
    )

    plt.xticks(time_data['max_depth'])  # X-Achse mit max_depth-Werten
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "execution_time_plot.png"))
    plt.clf()


# CPU Usage Plot als Säulendiagramm
plot_metric_bar("cpu_usage", "CPU-Auslastung (%)", "cpu_usage_bar_plot.png")

# Memory Usage Plot als Säulendiagramm
plot_metric_bar("memory_usage", "Arbeitsspeicherverbrauch (MB)", "memory_usage_bar_plot.png")

# Execution Time Plot als Säulendiagramm
plot_execution_time_bar()

# Number of Threads Plot als Säulendiagramm
plot_metric_bar("num_threads", "Thread-Anzahl", "num_threads_bar_plot.png")

print("Plotting with bar charts done")
