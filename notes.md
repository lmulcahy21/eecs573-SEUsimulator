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