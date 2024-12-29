import subprocess
import time
import os
import csv
import yaml
import numpy as np

# Parameter, die konstant bleiben
ALGORITHMS = ["platform", "virtual", "coroutines", "goroutines"]
INTERFACE_TYPE = "SQL" #"REST", "SQL"

NUMBER_OF_ACCOUNTS = "1000"
NUMBER_OF_TRANSACTIONS = "100000"
DELAY_TRANSACTION = 0.1

# Verzeichnisse für die Dateien
MEASUREMENTS_DIR = os.path.join(os.getcwd(), "measurements")

def run_bank_data_generator(number_of_accounts, number_of_transactions):
    jar_path = "./bankDataGenerator.jar"
    subprocess.run(["java", "-jar", jar_path, number_of_accounts, number_of_transactions], capture_output=True, text=True)
    print("Data generateted")

def modify_docker_compose_file(algorithm, interface, number_of_accounts, number_of_transactions, delay_transaction):
    # Lese den Inhalt der Vorlage
    docker_compse_file = ""
    if interface == "REST":
        docker_compse_file = "docker-compose_templateREST.yaml"
    elif interface == "SQL":
        docker_compse_file = "docker-compose_templateSQL.yaml"

    with open(docker_compse_file, "r") as file:
        data = yaml.safe_load(file)

    # Aktualisiere den Algorithmus und die Schnittstelle
    data['services']['bank']['volumes'] = ['./bankData:/bankData']
    # Java: Platform Threads
    if algorithm == "platform":
        data["services"]["bank"]["image"] = "bank-java"
        data["services"]["bank"]["environment"]["ALGORITHM"] = "PLATFORM"
        if interface == "SQL":
            data["services"]["bank"]["environment"]["INTERFACE_TYPE"] = "JDBC"
            data["services"]["bank"]["environment"]["DB_HOST"] = "postgres"

    # Java: Virtual Threads
    elif algorithm == "virtual":
        data["services"]["bank"]["image"] = "bank-java"
        data["services"]["bank"]["environment"]["ALGORITHM"] = "VIRTUAL"
        if interface == "SQL":
            data["services"]["bank"]["environment"]["INTERFACE_TYPE"] = "JDBC"
            data["services"]["bank"]["environment"]["DB_HOST"] = "postgres"

    # Kotlin: Coroutines
    elif algorithm == "coroutines":
        data["services"]["bank"]["image"] = "bank-kotlin"
        data["services"]["bank"]["environment"]["ALGORITHM"] = "COROUTINE"
        if interface == "SQL":
            data["services"]["bank"]["environment"]["INTERFACE_TYPE"] = "R2DBC"
            data["services"]["bank"]["environment"]["DB_HOST"] = "postgres"
    
    # Go: Goroutines
    elif algorithm == "goroutines":
        data["services"]["bank"]["image"] = "bank-go"
        data["services"]["bank"]["environment"]["ALGORITHM"] = "GOROUTINE"
        data['services']['bank']['volumes'] = ['./bankData:/app/bankData']
        if interface == "SQL":
            data["services"]["bank"]["environment"]["INTERFACE_TYPE"] = "PGX"
            data["services"]["bank"]["environment"]["DB_HOST"] = "postgres"
    
    # Aktualisiere die Anzahl der Konten, Transaktionen und Verzögerung
    data["services"]["bank"]["environment"]["NUMBER_OF_ACCOUNTS"] = number_of_accounts
    data["services"]["bank"]["environment"]["NUMBER_OF_TRANSACTIONS"] = number_of_transactions
    data["services"]["bank"]["environment"]["DELAY_TRANSACTION"] = str(delay_transaction)

    # Schreibe die aktualisierten Daten in die Datei
    with open("docker-compose_modify.yaml", "w") as file:
        yaml.dump(data, file, default_flow_style=False)

    print("Docker-Compose-Datei was modified successfully.")

# Funktion zum Aufzeichnen von CPU-, Speicher- und PIDs-Statistiken
def record_process_stats(service_name, writer, transactions):
    start_time = time.time()
    while True:

        # Container-Namen, die abgefragt werden sollen
        containers_to_check = [service_name, "postgres"]

        try:
            # Aufruf von docker stats
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", 
                "{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.PIDs}}"],
                capture_output=True,
                text=True,
                check=True
            )

            # Verarbeitung der Ausgabe
            all_stats = result.stdout.strip().splitlines()
            filtered_stats = {}

            for line in all_stats:
                # Teile die Ausgabe in Name, CPU, Mem und PIDs
                name, cpu, mem, pids = line.split(",", 3)
                if name in containers_to_check:
                    filtered_stats[name] = {
                        "CPU": float(cpu.strip('%')),
                        "Memory": mem.split('/')[0].strip().upper(),
                        "PIDs": int(pids.strip())
                    }
                    if "MIB" in filtered_stats[name]["Memory"]:
                        filtered_stats[name]["Memory"] = float(filtered_stats[name]["Memory"].replace("MIB", "").strip())
                    elif "GIB" in filtered_stats[name]["Memory"]:
                        filtered_stats[name]["Memory"] = float(filtered_stats[name]["Memory"].replace("GIB", "").strip()) * 1024

            # Überprüfe den Container-Status auf 'exited'
            inspect_result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Status}}", service_name],
                capture_output=True,
                text=True,
                check=True
            )

            container_status = inspect_result.stdout.strip()
            if container_status == 'exited':
                # Überprüfe den Exit-Code
                exit_code_result = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.ExitCode}}", service_name],
                    capture_output=True,
                    text=True,
                    check=True
                )
                exit_code = int(exit_code_result.stdout.strip())
                
                if exit_code == 0:
                    print(f"Container {service_name} has exited with Exit-Code 0. Monitoring will be stopped.")
                elif exit_code == 1:
                    print(f"Container {service_name} has exited with Exit-Code 1. Monitoring will be stopped.")
                else:
                    print(f"Container {service_name} has exited with Exit-Code {exit_code}. Monitoring will be stopped.")
                break

            elapsed_time = round(time.time() - start_time, 1)  # Verstrichene Zeit

            # Schreibe Messwerte in die CSV
            writer.writerow([transactions, elapsed_time, filtered_stats[service_name]["CPU"], filtered_stats[service_name]["Memory"], filtered_stats[service_name]["PIDs"], filtered_stats["postgres"]["CPU"]])
            print(f"Time: {elapsed_time}s, CPU: {filtered_stats[service_name]['CPU']}%, RAM: {filtered_stats[service_name]['Memory']}MB, PIDs: {filtered_stats[service_name]['PIDs']}, Postgres CPU: {filtered_stats['postgres']['CPU']}%")

        except subprocess.CalledProcessError as e:
            print(f"Error while running docker stats: {e}")
        except KeyboardInterrupt:
            print("Monitoring stopped.")
            break


def measure(algorithm, delay, execution_times):

    # Programm starten
    print(f"Start measurement for {algorithm} with delay {delay}")
    docker_compose_file = "docker-compose_modify.yaml"
    process = subprocess.Popen(
            ["docker-compose", "-f", docker_compose_file, "up"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

    # Zeilenweise Ausgabe prüfen
    for line in iter(process.stdout.readline, ""):
        line = line.strip()  # Leerzeichen am Anfang und Ende entfernen
        if line:  # Nur nicht-leere Zeilen ausgeben
            print(line)
        # Überprüfe auf die gewünschte Nachricht
        if "File imported." in line:
            break

    # Startzeit für Ausführung messen
    start_time = time.time()

    # CSV-Datei für Messwerte öffnen
    csv_file = os.path.join(MEASUREMENTS_DIR, f"measurement_log_{algorithm}.csv")
    with open(csv_file, 'a', newline='') as stats_file:
        writer = csv.writer(stats_file)
        if os.stat(csv_file).st_size == 0:
            # Header nur einmal schreiben, wenn Datei leer ist
            writer.writerow(['delay', 'timestamp', 'cpu_usage', 'memory_usage', 'num_threads', 'postgres_cpu'])

        # psutil Messung (CPU, Speicher und Threads)
        record_process_stats("bank-bank-1", writer, delay)

    # Endzeit nach der Ausführung messen
    end_time = time.time()
    execution_time = round(end_time - start_time, 1)

    # Speichere die Ausführungszeit für den jeweiligen Algorithmus in der Ausführungszeit-Liste
    execution_times[algorithm][delay] = execution_time

    print(f"Stop measurement for {algorithm} - Time: {execution_time}s")


def main():
    # Sicherstellen, dass der Ordner "measurements" existiert
    os.makedirs(MEASUREMENTS_DIR, exist_ok=True)

    # Öffne die Datei für die Ausführungszeiten
    TIME_LOG = os.path.join(MEASUREMENTS_DIR, "measurement_log_time.csv")
    with open(TIME_LOG, 'w', newline='') as time_file:
        time_writer = csv.writer(time_file)
        # Header für die Ausführungszeiten schreiben
        time_writer.writerow(['delay', 'virtual', 'platform', 'coroutines', 'goroutines'])

        # Dictionary für die Ausführungszeiten jedes Algorithmus
        execution_times = {
            'platform': {},
            'virtual': {},
            'coroutines': {},
            'goroutines': {}
        }

        for delay in np.arange(0.01, DELAY_TRANSACTION+0.001, 0.01):
            print(f"Number of delay set to: {delay}")

            run_bank_data_generator(NUMBER_OF_ACCOUNTS, NUMBER_OF_TRANSACTIONS)

            # Für jedes transactions messen wir die Ausführungszeit für jeden Algorithmus
            for algorithm in ALGORITHMS:
                
                # Passe Docker-Compose-Datei an
                modify_docker_compose_file(algorithm, INTERFACE_TYPE, NUMBER_OF_ACCOUNTS, NUMBER_OF_TRANSACTIONS, delay)

                # Führe die Messung für den aktuellen Algorithmus durch
                measure(algorithm, delay, execution_times)

                time.sleep(1)

            # Sobald alle Algorithmen für dieses transactions gemessen wurden, speichern wir die Daten
            row = [delay] + [execution_times[alg].get(delay, 'N/A') for alg in ALGORITHMS]

            time_writer.writerow(row)

if __name__ == "__main__":
    main()
