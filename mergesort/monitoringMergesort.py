import subprocess
import time
import os
import psutil
import csv
import platform

# Constants
ALGORITHMS = ["platform", "virtual", "coroutines", "goroutines"]
LIST_LENGTH = "10000000"
RUNS = "10"
WARMUP_RUNS = "0"
MAX_DEPTH = 4

# Directory setup
EXECUTABLES_DIR = os.path.join(os.getcwd(), "executables")
MEASUREMENTS_DIR = os.path.join(os.getcwd(), "measurements")

# File paths
JAR_FILE = os.path.join(EXECUTABLES_DIR, "mergesortJava.jar")
KOTLIN_FILE = os.path.join(EXECUTABLES_DIR, "mergesortKotlin.jar")
GOROUTINE_FILE = os.path.join(EXECUTABLES_DIR, "mergesortGo.exe") if platform.system() == "Windows" else os.path.join(EXECUTABLES_DIR, "mergesortGo")

def start_program(algorithm, max_depth):
    if algorithm == "coroutines":
        FILE = KOTLIN_FILE
        process = subprocess.Popen(
            ["java", "-Xms4g", "-Xmx4g", "-server", "-jar", FILE, algorithm, LIST_LENGTH, max_depth, RUNS, WARMUP_RUNS],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    elif algorithm == "goroutines":
        FILE = GOROUTINE_FILE
        env = os.environ.copy()
        env["GOMEMLIMIT"] = "4GiB"
        process = subprocess.Popen(
            [FILE, "-algorithm", algorithm, "-listLength", LIST_LENGTH, "-maxDepth", max_depth, "-runs", RUNS, "-warmUpRuns", WARMUP_RUNS],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
    else:
        FILE = JAR_FILE
        process = subprocess.Popen(
            ["java", "-Xms4g", "-Xmx4g", "-server", "-jar", FILE, algorithm, LIST_LENGTH, max_depth, RUNS, WARMUP_RUNS],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    return process

def record_process_stats(process, max_depth, writer):
    try:
        ps_process = psutil.Process(process.pid)
        start_time = time.time()
        ps_process.cpu_percent(interval=None)
        last_cpu_measurement_time = time.time()
        time.sleep(0.2)

        while ps_process.is_running():
            try:
                memory_usage = ps_process.memory_info().rss / (1024 * 1024)  # in MB
                num_threads = ps_process.num_threads()
                elapsed_time = round(time.time() - start_time, 1)

                cpu_usage = None
                if time.time() - last_cpu_measurement_time >= 2.0:
                    cpu_usage = ps_process.cpu_percent(interval=None) / psutil.cpu_count()
                    last_cpu_measurement_time = time.time()

                writer.writerow([max_depth, elapsed_time, cpu_usage, memory_usage, num_threads])
                time.sleep(0.2)

            except psutil.NoSuchProcess:
                print(f"Process {process.pid} ended unexpectedly.")
                break

    except psutil.NoSuchProcess:
        print(f"No process with PID {process.pid} found.")

def measure(algorithm, max_depth, execution_times):
    print(f"Starting program with algorithm: {algorithm}")
    process = start_program(algorithm, max_depth)

    while True:
        output = process.stdout.readline().decode()
        print(output)
        if "warum up runs finished" in output:
            break
        time.sleep(0.2)

    start_time = time.time()
    csv_file = os.path.join(MEASUREMENTS_DIR, f"measurement_log_{algorithm}.csv")
    with open(csv_file, 'a', newline='') as stats_file:
        writer = csv.writer(stats_file)
        if os.stat(csv_file).st_size == 0:
            writer.writerow(['max_depth', 'timestamp', 'cpu_usage', 'memory_usage', 'num_threads'])
        record_process_stats(process, max_depth, writer)

    execution_time = round(time.time() - start_time, 1)
    execution_times[algorithm][max_depth] = execution_time
    print(f"Measurement complete for PID: {process.pid}")

def main():
    os.makedirs(MEASUREMENTS_DIR, exist_ok=True)

    TIME_LOG = os.path.join(MEASUREMENTS_DIR, "measurement_log_time.csv")
    with open(TIME_LOG, 'w', newline='') as time_file:
        time_writer = csv.writer(time_file)
        time_writer.writerow(['max_depth', 'platform', 'virtual', 'coroutines', 'goroutines'])

        execution_times = {alg: {} for alg in ALGORITHMS}

        for max_depth in range(0, MAX_DEPTH):
            for algorithm in ALGORITHMS:
                measure(algorithm, str(max_depth), execution_times)
                time.sleep(5)

            row = [max_depth] + [execution_times[alg].get(str(max_depth), 'N/A') for alg in ALGORITHMS]
            time_writer.writerow(row)

if __name__ == "__main__":
    main()
