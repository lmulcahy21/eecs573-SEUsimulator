from nathan_parser import Netlist
from gen_testbench import gen_testbench
import random
#import numpy as np
#from scipy.stats import poisson
import subprocess
import os

# LAM = 50

VCS = "vcs"
VCS_FLAGS = "-sverilog -xprop=tmerge +vc -Mupdate -Mdir=build/csrc -line -full64 -kdb -lca -nc -debug_access+all+reverse +warn=noTFIPC +warn=noDEBUG_DEP +warn=noENUMASSIGN +warn=noLCA_FEATURES_ENABLED -timescale=1ps/1ps +vpi"
GATE_LIB = "/usr/caen/misc/class/eecs470/lib/verilog/lec25dscc25.v"
VCS_SRC = f"{GATE_LIB} generated/testbench.sv net_force.c"
SIM_EXE_NAME = "build/simv"

def sample_net(netlist: Netlist) -> str:
    return random.choice(netlist.wires_list)

# def sample_cycle_time(period_ns: int, lam: int) -> int:
#     period_ps = 1000 * period_ns
#     k_values = np.arange(1, period_ps + 1)
#     pmf = poisson.pmf(k_values, lam)

#     pmf_normalized = pmf / pmf.sum()

#     sample = np.random.choice(k_values, p=pmf_normalized)
#     return sample

# def sample_pulse_width() -> int:
#     # exponential or log-normal distribution?
#     # short much more common than longz
#     return 2

#def analyze_faults(netlist: Netlist, num_faults: int, clock_period_ns: int, setup_time_ns: int, hold_time_ns: int) -> float:

def analyze_faults(netlist: Netlist, num_faults: int) -> float:
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
    for _ in range(0, num_faults):
        net = sample_net(netlist)

        # make sure that if we get a wire with width > 1, we name it properly
        # e.g. we do A[0] instead of A_0.
        if netlist.wires[net].width > 1:
            # Split the string into two parts at the last underscore
            netname, netidx = net.rsplit('_', 1)
            visible_fault_nets.append(f"{netname}[{netidx}]")
        else:
            visible_fault_nets.append(net)

    # generate a testbench
    gen_testbench(netlist, visible_fault_nets, num_faults)

    # run simulation
    vcs_cmd = f"{VCS} {VCS_FLAGS} {VCS_SRC} {netlist.name}.vg -o {SIM_EXE_NAME}"
    os.makedirs("build", exist_ok=True)
    subprocess.run(vcs_cmd, shell=True)
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
        print("beginning analysis")
        print(f"FMR: {analyze_faults(netlist, 5000)}\n")

if __name__ == '__main__':
    print("starting")
    test_main()
