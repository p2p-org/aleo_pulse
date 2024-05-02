# Aleo pulse

### About:
Aleo-pulse is simple python script inspired by [sui-doctor](https://github.com/MystenLabs/sui-doctor) that allow you to check basic configuration of server/workstation, where aleo is executing. It can be useful if you don't have automation for server/workstation configuration and want to double-check that your setup is correct.

### Requirements:
- Python 3+
- Ubuntu
- Docker(for future version packed in docker)

### Checks:
- Time synced
- Net bandwidth
- Disk size
- Num CPU
- GPU
- Cpu governor
- Rmem_max
- Wmem_max

### Usage:
Aleo-pulse can be used with three flags for three different ways of aleo execution(as client, as prover, as validator)
For checking the system for validator setup, execute it: 

	git clone git@github.com:caligo8658/aleo_pulse.git
	./aleo-pulse.py validator

### TODO:
- Pack in docker
- Tests
- One 2 All connectivity test(in mainnet)
- ~Check swap off~

