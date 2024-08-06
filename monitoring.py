import subprocess
import time
import os
import signal
import psutil
import csv

# Parameter, die konstant bleiben
ALGORITHM = "virtual"
LIST_LENGTH = "10000000"
RUNS = "10"

# Name der JAR-Datei
JAR_FILE = "app.jar"

# Funktion zum Aufzeichnen von CPU- und Speicherverbrauch
def record_process_stats(pid, writer, chunk_number):

    process = psutil.Process(pid)
    start_time = time.time()  # Startzeitpunkt speicher
    process.cpu_percent()

    while process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
        measurement_time = time.time()

        cpu_usage = process.cpu_percent()
        memory_usage = process.memory_info().rss / (1024 * 1024)  # in MB
        num_threads = process.num_threads()
        elapsed_time = round(time.time() - start_time, 1)  # Verstrichene Zeit seit Start
        writer.writerow([chunk_number, elapsed_time, cpu_usage, memory_usage, num_threads])

        measurement_time = time.time() - measurement_time
        time.sleep(0.2 - measurement_time)

def measure(chunk_number, writer):
    # Java-Prozess starten
    print("Starte Java-Prozess")

    java_process = subprocess.Popen(
        ["java", "-jar", JAR_FILE, ALGORITHM, LIST_LENGTH, chunk_number, RUNS],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Warten auf "File imported." Meldung
    while True:
        output = java_process.stdout.readline().decode()
        print(output)
        if "File imported." in output:
            break
        time.sleep(0.2)

    #psutil Messung
    record_process_stats(java_process.pid, writer, chunk_number)

    print(f"Messung gestartet. PID: {java_process.pid}")



    print(f"Messung abgeschlossen. PID: {java_process.pid}")

def main():
    # Log-Datei für Messdaten
    MEASUREMENT_LOG = f"measurement_log.csv"
    #PLOT_FILE = f"{java_process.pid}.png"

    with open(MEASUREMENT_LOG, 'w') as f:
        writer = csv.writer(f)
        # Header schreiben
        writer.writerow(['chunk_number', 'timestamp', 
                         'cpu_usage', 'memory_usage', 'num_threads'])

        for chunks in range(0, 10):
            measure(str(chunks + 1), writer)

if __name__ == "__main__":
    main()