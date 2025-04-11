# NATHAN

## Installation guide

We recommend setting up a python virtual environment and require Python 3.10+. NATHAN was tested mainly on 3.11, but works on 3.10 as well.

In order to use NATHAN, we require PyVerilog and its dependencies. See [PyVerilog's installation instructions here](https://github.com/PyHDI/Pyverilog/blob/develop/README.md).
Note that Pyverilog also requires icarus verilog for their parser, which can be found (here)[https://github.com/steveicarus/iverilog].
When installing `iverilog` on shared machines, make sure when compiling to set the prefix properly to avoid needing root access.


Here is a brief installation guide, but results may vary.

```bash
$ python3.11 -m venv env
$ source env/bin/activate

(env) $ git clone https://github.com/steveicarus/iverilog.git
(env) $ cd ./iverilog/
(env) $ ./configure --prefix=/your/path/to/wherever/you/want/such_that_its_in_$PATH/we_used_/env/
(env) $ make
(env) $ make install

(env) $ python -m pip install pyverilog
(env) $ python nathan.py --module [SYNTHESIZED_MODULE.vg] --num_faults [N]
```


## Usage

```
--module: FILENAME
        Filename containing the structural verilog code for simulation.
        Currently expects files in the format of the Synopsis Design
        Compiler, as the specifications of output files from synthesis
        are sparsely documented. The parser *should* work for other
        formats, but expects .Q(output_net) to hold the output for a
        gate, so milage may vary.

--num_faults: Int
        Number of trials to run
```