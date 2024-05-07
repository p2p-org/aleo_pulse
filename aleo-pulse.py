#!/usr/bin/env python3

import os
import argparse
import sys
import speedtest
import shutil
import multiprocessing
import glob
import subprocess
import platform

parser = argparse.ArgumentParser(
    description="Aleo-pulse is a simple script that allow you to find typical misconfig errors")

parser.add_argument('mode', help='Mode of aleo (e.g. client, validator, prover)')

args = parser.parse_args()
aleo_modes = ['client', 'validator', 'prover']


def check_mode(mode, aleo_modes):
    if mode in aleo_modes:
        # mode OK, go on
        pass
    else:
        sys.exit("Mode is not OK. Mode should be 'client', 'validator' or 'prover'")


check_mode(args.mode, aleo_modes)  # check if args correct

MINIMUM_RMEM_MAX = 104857600
MINIMUM_WMEM_MAX = 104857600

OK_PREFIX = '[+] '
FAIL_PREFIX = '[-] '

Requirements = {
    'client':    {'cpu': 16, 'ram': 16, 'storage': 64,   'network': 100, 'gpu': 'none'},
    'prover':    {'cpu': 32, 'ram': 32, 'storage': 128,  'network': 250, 'gpu': 'CUDA'},
    'validator': {'cpu': 32, 'ram': 64, 'storage': 2000, 'network': 500, 'gpu': 'none'},
    }


def get_os():
    return platform.system()


def get_linux_distro():
    return platform.dist()[0].lower()


def check_aleo_client():
    try:
        output = subprocess.check_output(['aleo', '--version'], stderr=subprocess.STDOUT, text=True)
        print(f"{OK_PREFIX}Aleo Client is installed. Version: {output.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"{FAIL_PREFIX}Aleo Client is not installed.")


def check_aleo_dependencies():
    try:
        rust_version = subprocess.check_output(['rustc', '--version'], stderr=subprocess.STDOUT, text=True)
        print(f"{OK_PREFIX}Rust is installed. Version: {rust_version.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"{FAIL_PREFIX}Rust is not installed.")

    try:
        pkg_config_version = subprocess.check_output(['pkg-config', '--version'], stderr=subprocess.STDOUT, text=True)
        print(f"{OK_PREFIX}pkg-config is installed. Version: {pkg_config_version.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"{FAIL_PREFIX}pkg-config is not installed.")

    try:
        gcc_version = subprocess.check_output(['gcc', '--version'], stderr=subprocess.STDOUT, text=True)
        print(f"{OK_PREFIX}GCC is installed. Version: {gcc_version.strip().split()[0]}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"{FAIL_PREFIX}GCC is not installed. Please install it and try again.")

    if os.path.exists('/usr/lib/libssl.so') or os.path.exists('/usr/lib/x86_64-linux-gnu/libssl.so'):
        print(f"{OK_PREFIX}OpenSSL library is installed.")
    else:
        print(f"{FAIL_PREFIX}OpenSSL library is not installed.")


def check_timesyncd_synchronized():
    """Query the system to see if NTP has synchronized
     WARNING: this is a blocking subprocess."""

    os_name = get_os()
    if os_name == 'Linux':
        distro = get_linux_distro()
        if distro in ['ubuntu', 'debian', 'centos', 'redhat', 'fedora']:
            subprocess_instance = subprocess.Popen(['timedatectl'], stdout=subprocess.PIPE, universal_newlines=True)
            cmd_out, _error = subprocess_instance.communicate()

            list_of_parts = cmd_out.split('\n')
            string_val = list_of_parts[4].strip()
            list_of_strings = string_val.split(":")
            string_val = list_of_strings[1].strip()

            if string_val == "yes":
                print(f"{OK_PREFIX}Time is synchronized.")
                return True
            else:
                print(f"{FAIL_PREFIX}Time not synced. Check your NTP daemon.")
                return False
        else:
            print(f"{FAIL_PREFIX}Aleo-pulse unable to check NTP sync in your {distro} linux distro")
            return False
    elif os_name == 'Darwin':
        try:
            # Getting info about time server from the config
            time_server = None
            with open("/etc/ntp.conf", "r") as file:
                lines = file.readlines()
                for line in lines:
                    if line.startswith("server"):
                        time_server = line.split()[1]
                        break

            if time_server:
                print(f"{OK_PREFIX}Time server is specified: {time_server}")

                # Checking time offset with the specified server
                output = subprocess.check_output(['sntp', '-t', '1', time_server], stderr=subprocess.STDOUT, text=True)
                offset = float(output.split()[0])
                if abs(offset) < 1.0:  # Acceptable offset is 1 second
                    print(f"{OK_PREFIX}Time is synchronized. Offset: {offset} seconds.")
                    return True
                else:
                    print(f"{FAIL_PREFIX}Time is not synchronized. Offset: {offset} seconds.")
                    return False
            else:
                print(f"{FAIL_PREFIX}Time server is not specified.")
                return False

        except FileNotFoundError as e:
            print(f"{FAIL_PREFIX}Error: {e}")
            return False
        except subprocess.CalledProcessError as e:
            print(f"{FAIL_PREFIX}Failed to check time synchronization: {e}")
            return False
        except (IndexError, ValueError):
            print(f"{FAIL_PREFIX}Failed to parse sntp output.")
            return False
    else:
        print(f"{FAIL_PREFIX}Aleo-pulse doesn't support OS: {os_name}")
        return False


def check_swap():
    os_name = get_os()
    if os_name == 'Linux':
        distro = get_linux_distro()
        if distro in ['ubuntu', 'debian']:
            output = subprocess.getoutput("/usr/sbin/swapon -s")
        elif distro in ['centos', 'redhat', 'fedora']:
            output = subprocess.getoutput("/sbin/swapon -s")
        else:
            print(f"{FAIL_PREFIX}Aleo-pulse unable to check swap setting in your {distro} linux distro")
            return
    elif os_name == 'Darwin':
        output = subprocess.getoutput("sysctl vm.swapusage")
    else:
        print(f"{FAIL_PREFIX}Aleo-pulse doesn't support OS: {os_name}")
        return

    if output.strip() != '':
        print(f"{FAIL_PREFIX}Swap should be disabled for best performance.")
    else:
        print(f"{OK_PREFIX}Swap configuration is OK.")


def check_cpu_governor():
    os_name = get_os()
    if os_name == 'Linux':

        # Define the path to the scaling_governor file
        path = "/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"

        # Find all files that match the pattern
        governor_files = [f for f in glob.glob(path) if os.path.isfile(f)]

        # If there are no governor files, return True
        if not governor_files:
            print(f"{OK_PREFIX}No CPU governor detected")

        # Check each governor file to see if it is set to "performance"
        for file_path in governor_files:
            with open(file_path, "r") as f:
                governor = f.read().strip()
            if governor != "performance":
                print(f"{FAIL_PREFIX}CPU governor detected that is not set to performance")
    elif os_name == 'Darwin':
        output = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
        if "Apple M" in output:
            print("CPU governor check skipped for Apple Silicon")
        else:
            print("CPU governor check not supported for macOS")
    else:
        print(f"{FAIL_PREFIX}Aleo-pulse doesn't support OS: {os_name}")


def check_rmem_max():
    os_name = get_os()
    if os_name == 'Linux':
        try:
            output = subprocess.check_output(["sysctl", "-n", "net.core.rmem_max"], universal_newlines=True).strip()
            if int(output) >= MINIMUM_RMEM_MAX:
                print(f"{OK_PREFIX}Socket receive buffer OK")
            else:
                print(f"{FAIL_PREFIX}For best network performance, increase the maximum socket receive buffer size with `sudo sysctl -w net.core.rmem_max=104857600`")
        except subprocess.CalledProcessError:
            print(f"{FAIL_PREFIX}Failed to check rmem_max. Please check manually, should be more than {MINIMUM_RMEM_MAX}")
    elif os_name == 'Darwin':
        try:
            output = subprocess.check_output(["sysctl", "-n", "kern.ipc.maxsockbuf"], universal_newlines=True).strip()
            if int(output) >= MINIMUM_RMEM_MAX:
                print(f"{OK_PREFIX}Socket receive buffer OK")
            else:
                print(f"{FAIL_PREFIX}For best network performance, increase the maximum socket receive buffer size with `sudo sysctl -w kern.ipc.maxsockbuf=104857600`")
        except subprocess.CalledProcessError:
            print(f"{OK_PREFIX}Failed to check kern.ipc.maxsockbuf. Please check manually, should be more than {MINIMUM_RMEM_MAX}")
    else:
        print(f"{FAIL_PREFIX}Aleo-pulse doesn't support OS: {os_name}")

def check_wmem_max():
    os_name = get_os()
    if os_name == 'Linux':
        try:
            output = subprocess.check_output(["sysctl", "-n", "net.core.wmem_max"], universal_newlines=True).strip()
            if int(output) >= MINIMUM_WMEM_MAX:
                print(f"{OK_PREFIX}Maximum socket send buffer OK")
            else:
                print(f"{FAIL_PREFIX}For best network performance, increase the maximum socket send buffer size with `sudo sysctl -w net.core.wmem_max=104857600`")
        except subprocess.CalledProcessError:
            print(f"{FAIL_PREFIX}Failed to check wmem_max. Please check manually, should be more than {MINIMUM_WMEM_MAX}")
    elif os_name == 'Darwin':
        try:
            output = subprocess.check_output(["sysctl", "-n", "kern.ipc.maxsockbuf"], universal_newlines=True).strip()
            if int(output) >= MINIMUM_WMEM_MAX:
                print(f"{OK_PREFIX}Maximum socket send buffer OK")
            else:
                print(f"{FAIL_PREFIX}For best network performance, increase the maximum socket send buffer size with `sudo sysctl -w kern.ipc.maxsockbuf=104857600`")
        except subprocess.CalledProcessError:
            print(f"{FAIL_PREFIX}Failed to check kern.ipc.maxsockbuf. Please check manually, should be more than {MINIMUM_WMEM_MAX}")
    else:
        print(f"{FAIL_PREFIX}Aleo-pulse doesn't support OS: {os_name}")

def check_disk_size(mode=args.mode):
    total = shutil.disk_usage("/")[0]
    aleo_disk_size = total // 2**30

    if aleo_disk_size < Requirements[mode]['storage']:
        print(f"{FAIL_PREFIX}Storage for {mode} should be more than: {Requirements[mode]['storage']}")
    else:
        print(f"{OK_PREFIX}Storage size fits: {aleo_disk_size} Gb")


def check_num_cpus(mode=args.mode):
    cpu_count = multiprocessing.cpu_count()
    if cpu_count < Requirements[mode]['cpu']:
        print(f"{FAIL_PREFIX}CPU count for {mode} should be more than: {Requirements[mode]['cpu']}")
    else:
        print(f"{OK_PREFIX}CPU count fits: {cpu_count}")


def check_gpu(mode=args.mode):
    if mode == 'prover':
        os_name = get_os()
        if os_name == 'Linux':
            try:
                output = subprocess.check_output(['nvidia-smi'], stderr=subprocess.STDOUT, text=True)
                if 'NVIDIA-SMI' in output:
                    gpu_info = output.split('\n')[5].split('|')[1].strip()
                    print(f"{OK_PREFIX}GPU detected: {gpu_info}")

                    # Check CUDA compatibility
                    if 'CUDA' in output:
                        print(f"{OK_PREFIX}GPU is CUDA compatible.")
                        return True
                    else:
                        print(
                            f"{FAIL_PREFIX}GPU is not CUDA compatible. Please check https://developer.nvidia.com/cuda-gpus for compatible GPUs.")
                        return False
                else:
                    print(
                        f"{FAIL_PREFIX}No NVIDIA GPU detected. Please check https://developer.nvidia.com/cuda-gpus for compatible GPUs.")
                    return False
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(
                    f"{FAIL_PREFIX}Failed to detect GPU. Please ensure you have an NVIDIA GPU and the NVIDIA driver is installed.")
                return False
        elif os_name == 'Darwin':
            try:
                output = subprocess.check_output(['system_profiler', 'SPDisplaysDataType'], stderr=subprocess.STDOUT, text=True)
                if 'Vendor: NVIDIA' in output:
                    gpu_info = output.split('Vendor: NVIDIA')[1].split('\n')[0].strip()
                    print(f"{OK_PREFIX}GPU detected: {gpu_info}")
                    print(
                        f"{OK_PREFIX}Please ensure your NVIDIA GPU is CUDA compatible. Check https://developer.nvidia.com/cuda-gpus for compatible GPUs.")
                    return True
                else:
                    print(
                        f"{FAIL_PREFIX}No NVIDIA GPU detected. Please check https://developer.nvidia.com/cuda-gpus for compatible GPUs.")
                    return False
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"{FAIL_PREFIX}Failed to detect GPU. Please ensure you have an NVIDIA GPU.")
                return False
        else:
            print(f"{FAIL_PREFIX}GPU check is not supported on your OS: {os_name}")
            return False
    else:
        print(f"{OK_PREFIX}GPU is not required for your mode.")
        return True


def detect_net_bandwidth():
    def bytes_to_mb(num_bytes):
        kb = 1024  # One Kilobyte is 1024 bytes
        mb = kb * 1024  # One MB is 1024 KB
        return int(num_bytes/mb)

    try:
        speed_test = speedtest.Speedtest()
        download_speed = bytes_to_mb(speed_test.download())
        upload_speed = bytes_to_mb(speed_test.upload())
        print(f"Download speed: {download_speed} MB/s")
        print(f"Upload speed: {upload_speed} MB/s")
        return upload_speed, download_speed
    except speedtest.ConfigRetrievalError:
        print(f"{FAIL_PREFIX}Failed to retrieve Speedtest configuration. Please check your network connection.")
        return None, None
    except speedtest.SpeedtestException as e:
        print(f"{FAIL_PREFIX}An error occurred while running Speedtest: {str(e)}")
        return None, None


def check_net(mode=args.mode):
    print("Running bandwidth test...")
    upload_speed, download_speed = detect_net_bandwidth()
    if upload_speed is None or download_speed is None:
        print("Skipping network bandwidth check due to errors.")
        return

    if upload_speed < Requirements[mode]['network']:
        print(f"{FAIL_PREFIX}Upload speed for {mode} should be more than: {Requirements[mode]['network']} MB/s")
    else:
        print(f"{OK_PREFIX}Upload speed fits: {upload_speed} MB/s")

    if download_speed < Requirements[mode]['network']:
        print(f"{FAIL_PREFIX}Download speed for {mode} should be more than: {Requirements[mode]['network']} MB/s")
    else:
        print(f"{OK_PREFIX}Download speed fits: {download_speed} MB/s")


# ------- End of checks ---

def check_pulse(mode):
    # print(Requirements['client']['cpu'])
    check_aleo_client()
    check_aleo_dependencies()
    check_timesyncd_synchronized()
    check_net(mode)
    check_disk_size(mode)
    check_num_cpus(mode)
    check_gpu(mode)
    check_cpu_governor()
    check_rmem_max()
    check_wmem_max()
    check_swap()


if __name__ == "__main__":
    check_pulse(args.mode)
