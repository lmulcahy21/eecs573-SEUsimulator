# installing iverilog

## virtual env

```bash
python3.11 -m venv env
source env/bin/activate
```

## install iverilog

```bash
git clone https://github.com/steveicarus/iverilog.git
cd ./iverilog/
./configure --prefix=/home/lmulcahy/microarch_eecs573/eecs573-SEUsimulator/env
make
make install
```

now the pyverilog parser should work



## ok now what

given adjency list of the graph, and parsed longest delay (tbd how doing this but dont sweat yet), what to do?
- sample?
- gen testbench
    - encoding and decoding outputs w/ AN encodings
- run sim
- get results
- profit


