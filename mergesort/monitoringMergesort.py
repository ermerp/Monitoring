import subprocess
import time
import os
import signal
import psutil
import csv

# Parameter, die konstant bleiben
ALGORITHMS = ["platform", "virtual", "coroutines", "goroutine"]
LIST_LENGTH = "10000000"
RUNS = "10"

# Datei für die Algorithmen
JAR_FILE = "mergesortJava.jar"
KOTLIN_FILE = "mergesortKotlin.jar"
GOROUTINE_FILE = "./mergesortGo"

# Funktion zum Aufzeichnen von CPU- und Speicherverbrauch
def record_process_stats(pid, writer, chunk_number):
    process = psutil.Process(pid)
    start_time = time.time()  # Startzeitpunkt speichern
    process.cpu_percent()

    while process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
        measurement_time = time.time()

        cpu_usage = process.cpu_percent(interval=None)
        memory_usage = process.memory_info().rss / (1024 * 1024)  # in MB
        num_threads = process.num_threads()
        elapsed_time = round(time.time() - start_time, 1)  # Verstrichene Zeit seit Start
        writer.writerow([chunk_number, elapsed_time, cpu_usage, memory_usage, num_threads])

        measurement_time = time.time() - measurement_time
        time.sleep(0.2 - measurement_time)

def measure(ALGORITHM, chunk_number, writer):
    # Programm starten
    print(f"Starte Programm mit Algorithmus: {ALGORITHM}")

    # Auswahl der Datei basierend auf dem Algorithmus
    if ALGORITHM == "coroutines":
        FILE = KOTLIN_FILE
        process = subprocess.Popen(
            ["java", "-jar", FILE, ALGORITHM, LIST_LENGTH, chunk_number, RUNS],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    elif ALGORITHM == "goroutine":
        FILE = GOROUTINE_FILE
        process = subprocess.Popen(
            [FILE, "-algorithm", ALGORITHM, "-listLength", LIST_LENGTH, "-chunkNumber", chunk_number, "-runs", RUNS],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    else:
        FILE = JAR_FILE
        process = subprocess.Popen(
            ["java", "-jar", FILE, ALGORITHM, LIST_LENGTH, chunk_number, RUNS],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    # Warten auf "File imported." Meldung
    while True:
        output = process.stdout.readline().decode()
        print(output)
        if "File imported." in output:
            break
        time.sleep(0.2)

    # psutil Messung
    record_process_stats(process.pid, writer, chunk_number)

    print(f"Messung gestartet. PID: {process.pid}")
    print(f"Messung abgeschlossen. PID: {process.pid}")

def main():
    for ALGORITHM in ALGORITHMS:
        # Log-Datei für Messdaten
        MEASUREMENT_LOG = f"measurement_log_{ALGORITHM}.csv"

        with open(MEASUREMENT_LOG, 'w', newline='') as f:
            writer = csv.writer(f)
            # Header schreiben
            writer.writerow(['chunk_number', 'timestamp', 'cpu_usage', 'memory_usage', 'num_threads'])

            #for chunks in range(999, 10001, 1000):
            for chunks in range(0, 10):
                measure(ALGORITHM, str(chunks + 1), writer)

if __name__ == "__main__":
    main()
