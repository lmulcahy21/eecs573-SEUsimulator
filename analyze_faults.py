from nathan_parser import Netlist, parse_netlist
from gen_testbench import gen_testbench
import random
import numpy as np
import subprocess
import os
from typing import List, Tuple

# LAM = 50

VCS = "vcs"
VCS_FLAGS = "-sverilog -xprop=tmerge +vc -Mupdate -Mdir=build/csrc -line -full64 -kdb -lca -nc -debug_access+all+reverse +warn=noTFIPC +warn=noDEBUG_DEP +warn=noENUMASSIGN +warn=noLCA_FEATURES_ENABLED -timescale=1ps/1ps +vpi"
GATE_LIB = "/usr/caen/misc/class/eecs470/lib/verilog/lec25dscc25.v"
VCS_SRC = f"{GATE_LIB} generated/testbench.sv net_force.c"
SIM_EXE_NAME = "build/simv"

# TODO: tune these parameters
PULSE_WIDTH_MEAN = 5000
PULSE_WIDTH_STDEV = 500

class Pulse:
    def __init__(self, start_time_ps: int, end_time_ps: int):
        self.start_time_ps = start_time_ps
        self.end_time_ps = end_time_ps

class TimingInfo:
    def __init__(self, clock_period_ns: float, setup_time_ns: float, hold_time_ns: float):
        self.clock_period_ns = clock_period_ns
        self.clock_period_ps = clock_period_ns * 1000

        self.setup_time_ns = setup_time_ns
        self.setup_time_ps = setup_time_ns * 1000

        self.hold_time_ns = hold_time_ns
        self.hold_time_ps = hold_time_ns * 1000

def sample_net_index(wire_list: List[str]) -> int:
    # sample a net to modify from a uniform dist
    return random.randint(0, len(wire_list) - 1)

# sample a net to modify from a uniform dist
def sample_net(wire_list: List[str]) -> Tuple[str, int]:
    idx = sample_net_index(wire_list)
    return wire_list[idx], idx

# sample start time in ps from 0 to clock_period from a uniform dist
def sample_cycle_time(period_ns: int) -> int:
    return random.randint(0, period_ns * 1000)

# sample pulse width from a gaussian dist
def sample_pulse_width() -> int:
    return np.round(np.random.normal(PULSE_WIDTH_MEAN, PULSE_WIDTH_STDEV, 1))


def analyze_faults(netlist: Netlist, num_faults: int, clock_period_ns: float, setup_time_ns: float, hold_time_ns: float) -> float:
    for _ in range(0, num_faults):
        start_time_ps = sample_cycle_time(clock_period_ns)
        width_ps = sample_pulse_width()
        end_time_ps = start_time_ps + width_ps

        pulse = Pulse(start_time_ps, end_time_ps)
        timing_info = TimingInfo(clock_period_ns, setup_time_ns, hold_time_ns)

        if masked_by_timing(pulse, timing_info):
            pass
        elif violates_setup_hold(pulse, timing_info):
            pass
        else:
            # all good yo
            pass


    return

def analyze_faults(netlist: Netlist, num_faults: int, args) -> float:
    # sample nets, start times, and widths for each fault
    # this is timing stuff do this later
    # visible_fault_nets = []
    # masked_faults_timing = 0
    # metastable_faults = 0

    # for _ in range(0, num_faults):
    #     start_time_ps = sample_cycle_time(clock_period_ns, LAM)
    #     width_ps = sample_pulse_width()
    #     end_time_ps = start_time_ps + width_ps

    #     clock_period_ps = clock_period_ns * 1000
    #     setup_time_ps = setup_time_ns * 1000
    #     hold_time_ps = hold_time_ns * 1000
    #     setup_threshold_ps = clock_period_ps - setup_time_ps
    #     hold_threshold_ps = hold_time_ps
    #     # statically analyze timing information
    #     # determine which faults will never be seen
    #     if start_time_ps > hold_threshold_ps and end_time_ps < setup_threshold_ps:
    #         masked_faults_timing += 1

    #     # determine which faults will cause metastability
    #     elif start_time_ps < hold_threshold_ps or start_time_ps > setup_threshold_ps or \
    #         end_time_ps < hold_threshold_ps or end_time_ps > setup_threshold_ps:
    #         metastable_faults += 1

    #     # simulate all other faults by generating testbench
    #     else:
    #         net = sample_net(netlist) #TODO: make sure that if you get an input/output wire (i.e. it has width > 0), you gen with brackets
    #         visible_fault_nets.append(net)

    # sample nets
    visible_fault_nets = []
    filtered_wire_list = wire_names = [v.name for (k, v) in netlist.wires.items() if not v.is_output]
    wire_name_to_index = {
        v.name: i for i, (k, v) in enumerate(netlist.wires.items())
    }
    for _ in range(0, num_faults):
        net_name, net_idx = sample_net(filtered_wire_list)
        visible_fault_nets.append(wire_name_to_index[net_name])
    # write sampled indices to file
    INDEX_FILENAME= f"{os.getcwd()}/generated/{netlist.name}_net_indices_hex.gen"
    with (open(f"generated/{netlist.name}_net_indices_hex.gen", "w")) as f:
        for i in range(0, len(visible_fault_nets)):
            f.write(f"{visible_fault_nets[i]:04x}\n")

    # generate a testbench
    if not args.sim_only:
        gen_testbench(netlist, visible_fault_nets, num_faults)

        # Compile simulation
        vcs_cmd = f"{VCS} {VCS_FLAGS} {VCS_SRC} {args.module} -o {SIM_EXE_NAME}"
        print("Checking build directory...")
        try:
            os.makedirs("build", exist_ok=True)
        except Exception as e:
            print(f"Error creating/using build directory: {e}")
            return -1
        print(f"@@ Running vcs ({vcs_cmd})")

        subprocess.run(vcs_cmd, shell=True)
    # ensure testbench exists
    if not os.path.exists(f"generated/testbench.sv"):
        print("Testbench generation failed")
        return -1
    # run simulation
    print(f"@@ Running testbench ./{SIM_EXE_NAME}")
    subprocess.run(f"./{SIM_EXE_NAME}")

    # calculate masking ratio
    num_masked_faults = 0
    with open("generated/tb_output.txt", "r") as f:
        num_masked_faults = int(f.read().strip())

    fault_mask_ratio = num_masked_faults / num_faults

    return fault_mask_ratio

def test_main():
    netlists = parse_netlist("full_adder_64bit.vg")
    for module_name, netlist in netlists:
        print(f"FMR: {analyze_faults(netlist, 5000)}\n")

if __name__ == '__main__':
    test_main()
