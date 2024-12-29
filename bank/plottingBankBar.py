import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

# Verzeichnisse für die Daten, Plots und aggregierte Daten
MEASUREMENTS_DIR = os.path.join(os.getcwd(), "measurements")
PLOTS_DIR = os.path.join(os.getcwd(), "plots")
AGGREGATED_DIR = os.path.join(os.getcwd(), "aggregated")

# Sicherstellen, dass die Ordner existieren
os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(AGGREGATED_DIR, exist_ok=True)

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

for ALGORITHM, csv_file, color in zip(algorithms, csv_files, colors):
    data = pd.read_csv(csv_file)
    
    # Konvertieren der Spalten in numerische Werte
    data['delay'] = pd.to_numeric(data['delay'], errors='coerce')
    data['cpu_usage'] = pd.to_numeric(data['cpu_usage'], errors='coerce') / 4  # CPU-Werte durch 4 teilen
    data['memory_usage'] = pd.to_numeric(data['memory_usage'], errors='coerce')
    data['num_threads'] = pd.to_numeric(data['num_threads'], errors='coerce')
    data['postgres_cpu'] = pd.to_numeric(data['postgres_cpu'], errors='coerce') / 3  # Optional: auch durch 4 teilen, falls nötig
    
    # Maximale und durchschnittliche Werte berechnen
    max_values = data.groupby('delay').agg({
        'cpu_usage': 'max',
        'memory_usage': 'max',
        'num_threads': 'max',
        'postgres_cpu': 'max'  # Neu hinzugefügt
    }).reset_index()

    mean_values = data.groupby('delay').agg({
        'cpu_usage': 'mean',
        'memory_usage': 'mean',
        'num_threads': 'mean',
        'postgres_cpu': 'mean'  # Neu hinzugefügt
    }).reset_index()

    max_values_dict[ALGORITHM] = max_values
    mean_values_dict[ALGORITHM] = mean_values


# Zusätzliche Daten für Ausführungszeiten einlesen
time_data = pd.read_csv(TIME_LOG)
time_data['delay'] = pd.to_numeric(time_data['delay'], errors='coerce')
time_data['virtual'] = pd.to_numeric(time_data['virtual'], errors='coerce')
time_data['platform'] = pd.to_numeric(time_data['platform'], errors='coerce')
time_data['coroutines'] = pd.to_numeric(time_data['coroutines'], errors='coerce')
time_data['goroutines'] = pd.to_numeric(time_data['goroutines'], errors='coerce')

# Funktion zum Abrunden auf null Nachkommastellen
def round_to_zero(value):
    return int(value)

# Daten für alle Algorithmen zusammenfassen und in CSV-Dateien speichern
def save_aggregated_csv(metric, metric_name):
    aggregated_data = pd.DataFrame()

    for ALGORITHM in algorithms:
        max_values = max_values_dict[ALGORITHM]
        mean_values = mean_values_dict[ALGORITHM]

        # Kombinieren von max und mean Werten
        combined = pd.DataFrame({
            'delay': max_values['delay'],
            f'{ALGORITHM}_max_{metric_name}': max_values[metric].apply(round_to_zero),
            f'{ALGORITHM}_mean_{metric_name}': mean_values[metric].apply(round_to_zero)
        })

        if aggregated_data.empty:
            aggregated_data = combined
        else:
            aggregated_data = pd.merge(aggregated_data, combined, on='delay', how='outer')

    # Speichern der aggregierten Daten in einer CSV-Datei
    aggregated_data.to_csv(os.path.join(AGGREGATED_DIR, f"{metric_name}_aggregated.csv"), index=False)

# Speichern der aggregierten Werte für CPU, Memory und Threads
save_aggregated_csv('cpu_usage', 'cpu_usage')
save_aggregated_csv('memory_usage', 'memory_usage')
save_aggregated_csv('num_threads', 'num_threads')
save_aggregated_csv('postgres_cpu', 'postgres_cpu')

print("Aggregated CSV files have been created in the 'aggregated' folder.")

# Speichern der Ausführungszeit-Daten für alle Algorithmen
execution_time_aggregated = pd.DataFrame({
    'delay': time_data['delay'], 
    'virtual_execution_time': time_data['virtual'],
    'platform_execution_time': time_data['platform'],
    'coroutines_execution_time': time_data['coroutines'],
    'goroutines_execution_time': time_data['goroutines']
})
execution_time_aggregated.to_csv(os.path.join(AGGREGATED_DIR, "execution_time_aggregated.csv"), index=False)

# Funktion für das Plotten von Metriken als Säulendiagramm
def plot_metric_bar(metric, ylabel, filename):
    plt.figure(figsize=(12, 6))
    
    width = 0.2  # Breite der Balken
    num_algorithms = len(algorithms)
    messpunkte = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]  # Messpunkte für die X-Achse
    x_positions = range(len(messpunkte))  # Gleichmäßig verteilte X-Positionen
    
    for i, (ALGORITHM, color) in enumerate(zip(algorithms, colors)):
        max_values = max_values_dict[ALGORITHM]
        mean_values = mean_values_dict[ALGORITHM]
        
        # Mapping von 'delay' auf gleichmäßige X-Positionen
        positions = [pos + (i - (num_algorithms - 1) / 2) * width for pos in x_positions]
        
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

    plt.title(f'{ylabel} mit Maximal- und Mittelwerten pro Messpunkt')
    plt.xlabel('Messpunkte (delay)')
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
    
    # Gleichmäßige Verteilung der Labels auf der X-Achse
    plt.xticks(x_positions, labels=messpunkte)
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, filename))
    plt.clf()


# Plot für Ausführungsdauer als Säulendiagramm erstellen
def plot_execution_time_bar():
    plt.figure(figsize=(12, 6))
    
    width = 0.2  # Breite der Balken
    num_algorithms = len(algorithms)
    messpunkte = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100] # Messpunkte für die X-Achse
    x_positions = range(len(messpunkte))  # Gleichmäßig verteilte X-Positionen
    
    for i, (ALGORITHM, color) in enumerate(zip(algorithms, colors)):
        positions = [pos + (i - (num_algorithms - 1) / 2) * width for pos in x_positions]
        
        # Zeichne die Balken
        plt.bar(
            positions,
            time_data[ALGORITHM],  # Höhe der Balken
            width=width,
            label=labels[ALGORITHM],
            color=color,
            alpha=0.7
        )

    plt.title('Ausführungsdauer pro Messpunkt')
    plt.xlabel('Messpunkte (delay)')
    plt.ylabel('Ausführungsdauer (s)')

    # Positioniere die Legende unter dem Diagramm
    plt.legend(
        title="Legende", 
        loc="upper center", 
        bbox_to_anchor=(0.5, -0.2),
        ncol=4,
        columnspacing=1,
        handlelength=2
    )

    # Gleichmäßige Verteilung der Labels auf der X-Achse
    plt.xticks(x_positions, labels=messpunkte)
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

# PostgreSQL CPU Usage Plot als Säulendiagramm
plot_metric_bar("postgres_cpu", "PostgreSQL CPU-Auslastung (%)", "postgres_cpu_bar_plot.png")

print("Plotting with bar charts done")
