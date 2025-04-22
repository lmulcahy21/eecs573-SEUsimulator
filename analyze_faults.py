from nathan_parser import Netlist, parse_netlist, GraphWire
from gen_testbench import gen_testbench
import random
import numpy as np
import subprocess
import os
from typing import List, Tuple
from nathan_types import TimingInfo

VCS = "vcs"
VCS_FLAGS = "-sverilog -xprop=tmerge +vc -Mupdate -Mdir=build/csrc -line \
             -full64 -kdb -lca -nc -debug_access+all+reverse +warn=noTFIPC \
             +warn=noDEBUG_DEP +warn=noENUMASSIGN +warn=noLCA_FEATURES_ENABLED \
             -timescale=1ps/1ps +vpi +sdfverbose  +transport_path_delays +pulse_e/0 +pulse_r/0 +transport_int_delays +pulse_int_e/0 +pulse_int_r/0"
GATE_LIB = "/usr/caen/misc/class/eecs470/lib/verilog/lec25dscc25.v"
VCS_SRC = f"{GATE_LIB} generated/testbench/testbench.sv net_force.c"
SIM_EXE_NAME = "build/simv"

def analyze_faults(netlist: Netlist, timing_info: TimingInfo, num_faults: int, sdf_filename: str):
    # generate a testbench
    gen_testbench(netlist, timing_info, num_faults, sdf_filename)

    # run simulation
    vcs_cmd = f"{VCS} {VCS_FLAGS} {VCS_SRC} {netlist.filepath} -o {SIM_EXE_NAME}"
    os.makedirs("build", exist_ok=True)
    subprocess.run(vcs_cmd, shell=True)
    subprocess.run(f"./{SIM_EXE_NAME}")