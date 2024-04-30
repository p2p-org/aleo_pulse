#!/usr/bin/python3
import os
import argparse
import sys
import subprocess
import speedtest
import shutil
import multiprocessing
import glob
import subprocess


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

check_mode(args.mode, aleo_modes) # check if args correct

MINIMUM_RMEM_MAX = 104857600
MINIMUM_WMEM_MAX = 104857600

Requirements = {
    'client':    {'cpu':16, 'ram':16, 'storage': 64,   'network': 100, 'gpu': 'none'},
    'prover':    {'cpu':32, 'ram':32, 'storage': 128,  'network': 250, 'gpu': 'CUDA'},
    'validator': {'cpu':32, 'ram':64, 'storage': 2000, 'network': 500, 'gpu': 'none'},
    }

def check_timesyncd_synchronized():
    """Query the system to see if NTP has synchronized
     WARNING: this is a blocking subprocess."""

    subprocess_instance = subprocess.Popen(['timedatectl'], stdout=subprocess.PIPE,
                                           universal_newlines=True)
    cmd_out, _error = subprocess_instance.communicate()

    list_of_parts = cmd_out.split('\n')
    string_val = list_of_parts[4].strip()
    list_of_strings = string_val.split(":")
    string_val = list_of_strings[1].strip()

    if string_val == "yes":
        print("Check time synced: ok")
        return True
    else:
        print("Time not synced. Check your NTP daemon")
        return False


def detect_net_bandwith():
    def bytes_to_mb(bytes):
        KB = 1024 # One Kilobyte is 1024 bytes
        MB = KB * 1024 # One MB is 1024 KB
        return int(bytes/MB)

    speed_test = speedtest.Speedtest()
    download_speed = bytes_to_mb(speed_test.download())
    upload_speed = bytes_to_mb(speed_test.upload())
    print("Download speed:", download_speed, "MB/s\n"
          "Upload speed:", upload_speed, "MB")
    return upload_speed, download_speed

def check_net(mode = args.mode):
    upload_speed, download_speed = detect_net_bandwith()
    if upload_speed < Requirements[mode]['network']:
        print("Upload speed for", mode, "should be more than:", Requirements[mode]['network'])
    else:
        print("Upload speed fits:", upload_speed, "Mb")

    if upload_speed < Requirements[mode]['network']:
        print("Download speed for", mode, "should be more than:", Requirements[mode]['network'])
    else:
        print("Download speed fits:", download_speed, "Mb")

def check_disk_size(mode = args.mode):
    total = shutil.disk_usage("/")[0]
    aleo_disk_size = total // 2**30 

    if aleo_disk_size < Requirements[mode]['storage']:
        print("Storage for", mode, "should be more than:", Requirements[mode]['storage'])
    else: 
        print("Storage size fits:", aleo_disk_size, "Gb")


def check_num_cpus(mode = args.mode):
    cpu_count = multiprocessing.cpu_count()
    if cpu_count < Requirements[mode]['cpu']:
        print("CPU count for", mode, "should be more than:", Requirements[mode]['cpu'])
    else: 
        print("CPU count fits:", cpu_count)


def check_gpu(mode = args.mode):
    if mode == 'prover':
        print("Check your GPU fits here: https://developer.nvidia.com/cuda-gpus")
    else: 
        print("In your mode GPU does not required")

def check_cpu_governor():
    # Define the path to the scaling_governor file
    path = "/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"

    # Find all files that match the pattern
    governor_files = [f for f in glob.glob(path) if os.path.isfile(f)]

    # If there are no governor files, return True
    if not governor_files:
        print("no governor detected")

    # Check each governor file to see if it is set to "performance"
    for file_path in governor_files:
        with open(file_path, "r") as f:
            governor = f.read().strip()
        if governor != "performance":
            print("CPU governor detected that is not set to performance")

def check_rmem_max():
    output = os.system("cat /proc/sys/net/core/rmem_max")
    if int(output) >= MINIMUM_RMEM_MAX:
        print("Socket recieve buffer ok")
    else:
        print("for best network performance, increase maximum socket receive buffer size with `sysctl -w net.core.rmem_max=104857600`")


def check_wmem_max():
    output = os.system("cat /proc/sys/net/core/wmem_max")
    if int(output) >= MINIMUM_WMEM_MAX:
        print("Maximum socker send buffer ok")
    else:
        print("for best network performance, increase maximum socket send buffer size with `sysctl -w net.core.wmem_max=104857600`")

def check_swapoff():
    output = subprocess.getoutput("/usr/sbin/swapon -s")
    if output != '':
        print("Swap should be disabled for best perfomance. Use `swapoff -a` for disabling swap")
    else:
        print("Swap configuration is OK")


#------- End of checks ---

def check_pulse(mode):
    #print(Requirements['client']['cpu'])
    check_timesyncd_synchronized()
    check_net()
    check_disk_size()
    check_num_cpus()
    check_gpu()
    check_cpu_governor()
    check_rmem_max()
    check_wmem_max()
    check_swapoff()



if __name__ == "__main__":
    check_pulse(args.mode)

