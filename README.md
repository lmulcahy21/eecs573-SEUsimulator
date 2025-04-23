# NATHAN

## Installation guide

We recommend setting up a python virtual environment and require Python 3.10+. NATHAN was tested mainly on 3.11, but works on 3.10 as well.

In order to use NATHAN, we require PyVerilog and its dependencies. See [PyVerilog's installation instructions here](https://github.com/PyHDI/Pyverilog/blob/develop/README.md).
Note that Pyverilog also requires icarus verilog for their parser, which can be found (here)[https://github.com/steveicarus/iverilog].
When installing `iverilog` on shared machines, make sure when compiling to set the prefix properly to avoid needing root access.


Here is a brief installation guide after cloning, but mileage may vary.

```bash
# setup a virtual environment
$ python3.11 -m venv env
$ source env/bin/activate
# initialize submodules
(env) $ git submodule init
(env) $ git submodule update
# iVerilog installation guide: https://github.com/steveicarus/iverilog?tab=readme-ov-file#compiling-from-github
(env) $ cd ./iverilog/
(env) $ sh autoconf.sh
(env) $ ./configure --prefix=/path/to/your/env # We used env as a base for installing iverilog, ensure it is on $PATH and provide the absolute directory
(env) $ make
(env) $ make install
# install dependencies
(env) $ python -m pip install pyverilog numpy
# run NATHAN
(env) $ python nathan.py -m [SYNTHESIZED_MODULE.vg] -n [N] -l [path/to/cell_lib] -s [sdf_filepath] -p [Clock period] -st [setup time] -ht [hold time]
```


## Usage

```
  -h, --help            show this help message and exit
  -m FILE, --module FILE
                        Specify the input netlist
  -n NUM, --num_faults NUM
                        Specify the number of faults to inject
  -l LIB, --gate_library LIB
                        Specify the gate library to use for parsing and simulation
  -s FILE, --sdf FILE   Specify module timing information in Standard Data Format (SDF)
  -p PERIOD, --period PERIOD
                        Specify the clock period in nanoseconds (ns)
  -st TIME, --setup_time TIME
                        Specify the register setup time in nanoseconds (ns)
  -ht TIME, --hold_time TIME
                        Specify the register hold time in nanoseconds (ns)

```