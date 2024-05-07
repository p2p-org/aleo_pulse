# Aleo pulse

## About
Aleo-pulse is a simple Python script inspired by [sui-doctor](https://github.com/MystenLabs/sui-doctor) that allows you to check the basic configuration of a server/workstation where Aleo is being executed. It can be useful if you don’t have automation for server/workstation configuration and want to double-check that your setup is correct.

## Features

- Check time synchronization
- Check network bandwidth
- Check disk size
- Check number of CPUs
- Check GPU (for prover mode)
- Check CPU governor
- Check `rmem_max` and `wmem_max` kernel parameters
- Check swap configuration
- Check Aleo client and its dependencies

## Requirements

- Python 3+
- Speedtest-cli package: Install with `pip install speedtest-cli`
- Operating system: Ubuntu, Debian, CentOS, macOS
- Docker (for future versions packed in Docker)

## Installation

1. Clone the repository
    ```
    git clone https://github.com/caligo8658/aleo_pulse.git
    ```

2. Navigate to the project directory
    ```
    cd aleo-pulse
    ```

3. Install the speedtest-cli package
    ```
    pip uninstall speedtest
    pip install speedtest-cli
    ```

4. Make the script executable
    ```
    chmod +x aleo-pulse.py
    ```

## License

This project is licensed under the Apache 2 License.

## Usage

Run the script with the desired mode

    ./aleo-pulse.py MODE

Replace `MODE` with one of the following:

- `client`: Check configuration for running Aleo as a client
- `prover`: Check configuration for running Aleo as a prover
- `validator`: Check configuration for running Aleo as a validator

Example

    ./aleo-pulse.py validator

## TODO
- Pack in Docker
- Tests
- One-to-All Connectivity Test (in Mainnet)
- ~Ensure Swap is Turned Off~

