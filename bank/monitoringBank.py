import subprocess
import time
import os
import csv
import yaml

# Parameter, die konstant bleiben
ALGORITHMS = ["platform"]
#ALGORITHMS = ["platform", "virtual", "coroutines", "goroutines"]
INTERFACE_TYPE = "REST" #"REST", "SQL"

NUMBER_OF_ACCOUNTS = "1000"
NUMBER_OF_TRANSACTIONS = "300000"

# Verzeichnisse für die Dateien
MEASUREMENTS_DIR = os.path.join(os.getcwd(), "measurements")

def run_bank_data_generator(number_of_accounts, number_of_transactions):
    jar_path = "./bankDataGenerator.jar"
    subprocess.run(["java", "-jar", jar_path, number_of_accounts, number_of_transactions], capture_output=True, text=True)
    print("Data generateted")

def modify_docker_compose_file(algorithm, interface, number_of_accounts, number_of_transactions):
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
    
    # Aktualisiere die Anzahl der Konten und Transaktionen
    data["services"]["bank"]["environment"]["NUMBER_OF_ACCOUNTS"] = number_of_accounts
    data["services"]["bank"]["environment"]["NUMBER_OF_TRANSACTIONS"] = number_of_transactions

    # Schreibe die aktualisierten Daten in die Datei
    with open("docker-compose_modify.yaml", "w") as file:
        yaml.dump(data, file, default_flow_style=False)

    print("Docker-Compose-Datei wurde erfolgreich aktualisiert.")

# Funktion zum Aufzeichnen von CPU-, Speicher- und PIDs-Statistiken
def record_process_stats(service_name, writer, transactions):
    start_time = time.time()
    while True:
        try:
            # Führe docker stats aus und hole die Werte für CPU, Speicher und PIDs
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", 
                 "{{.CPUPerc}},{{.MemUsage}},{{.PIDs}}", service_name],
                capture_output=True,
                text=True,
                check=True
            )

            # Parsen der Ausgabe von docker stats
            output = result.stdout.strip()
            if not output:
                print(f"Service {service_name} nicht gefunden!")
                break

            cpu_usage, memory_usage, pids = output.split(",")
            cpu_usage = float(cpu_usage.strip('%'))  # Entferne das Prozentzeichen
            memory_usage = memory_usage.split('/')[0].strip().upper()  # Speicher extrahieren
            if "MB" in memory_usage:
                memory_usage = float(memory_usage.replace("MB", "").strip())
            elif "GB" in memory_usage:
                memory_usage = float(memory_usage.replace("GB", "").strip()) * 1024

            pids = int(pids.strip())  # PIDs in Integer umwandeln

            # Beende die Schleife, wenn PIDs 0 sind
            #if pids == 0:
            #    print(f"Alle Prozesse im Container {service_name} sind beendet (PIDs: {pids}). Überwachung wird beendet.")
            #    break

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
                    print(f"Container {service_name} hat mit Exit-Code 0 beendet. Überwachung wird beendet.")
                elif exit_code == 1:
                    print(f"Container {service_name} hat mit Exit-Code 1 beendet. Fehler im Container! Überwachung wird beendet.")
                else:
                    print(f"Container {service_name} hat mit Exit-Code {exit_code} beendet. Überwachung wird beendet.")
                break

            elapsed_time = round(time.time() - start_time, 1)  # Verstrichene Zeit

            # Schreibe Messwerte in die CSV
            writer.writerow([transactions, elapsed_time, cpu_usage, memory_usage, pids])
            print(f"Zeit: {elapsed_time}s, CPU: {cpu_usage}%, Speicher: {memory_usage}MB, PIDs: {pids}")

            #time.sleep(0.2)

        except subprocess.CalledProcessError as e:
            print(f"Fehler beim Ausführen von docker stats: {e}")
            break
        except KeyboardInterrupt:
            print("Überwachung beendet.")
            break


def measure(algorithm, transactions, execution_times):

    # Programm starten
    print(f"Starte Programm mit Algorithmus: {algorithm}")
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
            writer.writerow(['transactions', 'timestamp', 'cpu_usage', 'memory_usage', 'num_threads'])

        # psutil Messung (CPU, Speicher und Threads)
        record_process_stats("bank-bank-1", writer, transactions)

    # Endzeit nach der Ausführung messen
    end_time = time.time()
    execution_time = round(end_time - start_time, 1)

    # Speichere die Ausführungszeit für den jeweiligen Algorithmus in der Ausführungszeit-Liste
    execution_times[algorithm][transactions] = execution_time

    print(f"Messung abgeschlossen: {algorithm}")


def main():
    # Sicherstellen, dass der Ordner "measurements" existiert
    os.makedirs(MEASUREMENTS_DIR, exist_ok=True)

    # Öffne die Datei für die Ausführungszeiten
    TIME_LOG = os.path.join(MEASUREMENTS_DIR, "measurement_log_time.csv")
    with open(TIME_LOG, 'w', newline='') as time_file:
        time_writer = csv.writer(time_file)
        # Header für die Ausführungszeiten schreiben
        time_writer.writerow(['transactions', 'virtual', 'platform', 'coroutines', 'goroutines'])

        # Dictionary für die Ausführungszeiten jedes Algorithmus
        execution_times = {
            'platform': {},
            'virtual': {},
            'coroutines': {},
            'goroutines': {}
        }

        for transactions in range(100000, int(NUMBER_OF_TRANSACTIONS) + 1, 100000):
            print(f"Number of Transactions set to: {transactions}")

            run_bank_data_generator(NUMBER_OF_ACCOUNTS, str(transactions))

            # Für jedes transactions messen wir die Ausführungszeit für jeden Algorithmus
            for algorithm in ALGORITHMS:
                
                # Passe Docker-Compose-Datei an
                modify_docker_compose_file(algorithm, INTERFACE_TYPE, NUMBER_OF_ACCOUNTS, transactions)

                # Führe die Messung für den aktuellen Algorithmus durch
                measure(algorithm, transactions, execution_times)

                time.sleep(1)

            # Sobald alle Algorithmen für dieses transactions gemessen wurden, speichern wir die Daten
            row = row = [transactions]
            # Füge die Ausführungszeiten für jeden Algorithmus hinzu
            for algorithm in ALGORITHMS:
                row.append(execution_times[algorithm].get(str(transactions), 'N/A'))
            # Schreibe die Zeile in die CSV-Datei
            time_writer.writerow(row)

if __name__ == "__main__":
    main()
