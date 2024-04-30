# Aleo pulse

### About:
Aleo-pulse is simple python script inspired by [sui-doctor](https://github.com/MystenLabs/sui-doctor) that allow you to check basic configuration of server/workstation, where aleo is executing. It can be useful if you dont have automation for server/workstation configuration and want to doublecheck that your setup is correct.

### Requirements:
- python3+
- ubuntu
- docker(for future version packed in docker)

### Checks:
- time synced
- net bandwidth
- disk size
- num CPU
- GPU
- cpu governor
- rmem_max
- wmem_max

### Usage:
Aleo-pulse can be used with 3 flags for 3 different ways of aleo execution(as client, as prover, as validator)
For checking system for validator setup execute it: 

	git clone git@github.com:caligo8658/aleo_pulse.git
	./aleo-pulse.py validator

### TODO:
- pack in docker
- tests
- One 2 All connectivity test(in mainnet)
- ~check swap off~

