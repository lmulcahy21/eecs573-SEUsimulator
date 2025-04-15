from nathan_parser import Netlist, parse_netlist, GraphWire
from gen_testbench import gen_testbench
import random
import numpy as np
import subprocess
import os
from typing import List, Tuple

VCS = "vcs"
VCS_FLAGS = "-sverilog -xprop=tmerge +vc -Mupdate -Mdir=build/csrc -line \
             -full64 -kdb -lca -nc -debug_access+all+reverse +warn=noTFIPC \
             +warn=noDEBUG_DEP +warn=noENUMASSIGN +warn=noLCA_FEATURES_ENABLED \
             -timescale=1ps/1ps +vpi"
GATE_LIB = "/usr/caen/misc/class/eecs470/lib/verilog/lec25dscc25.v"
VCS_SRC = f"{GATE_LIB} generated/testbench/testbench.sv net_force.c"
SIM_EXE_NAME = "build/simv"

# TODO: tune these parameters
PULSE_WIDTH_MEAN_PS = 55
PULSE_WIDTH_STDEV_PS = 15

class Pulse:
    def __init__(self, net: str, start_time_ps: int, end_time_ps: int):
        self.net = net
        self.start_time_ps = start_time_ps
        self.end_time_ps = end_time_ps

class TimingInfo:
    def __init__(self, clock_period_ns: float, setup_time_ns: float, hold_time_ns: float):
        self.clock_period_ns = clock_period_ns
        self.clock_period_ps = np.round(clock_period_ns * 1000)

        self.setup_time_ns = setup_time_ns
        self.setup_time_ps = np.round(setup_time_ns * 1000)

        self.hold_time_ns = hold_time_ns
        self.hold_time_ps = np.round(hold_time_ns * 1000)

def sample_net_index(wire_list: List[str]) -> int:
    # sample a net to modify from a uniform dist
    return random.randint(0, len(wire_list) - 1)

# sample a net to modify from a uniform dist
def sample_net(wire_list: List[str]) -> Tuple[str, int]:
    idx = sample_net_index(wire_list)
    return wire_list[idx], idx

# sample start time in ps from 0 to clock_period from a uniform dist
# the timing of pulses is a poisson process but can be viewed as a uniform random
# sample from cycle to cycle
def sample_cycle_time(period_ns: int) -> int:
    return random.randint(0, period_ns * 1000)

# sample pulse width from a gaussian dist
# result is in PS
def sample_pulse_width() -> int:
    return np.round(np.random.normal(PULSE_WIDTH_MEAN_PS, PULSE_WIDTH_STDEV_PS, 1))

# determine whether a pulse is masked entirely from timing
# i.e. the pulse begins after the register hold time and settles by the
# setup time for the next clock. These pulses are never seen.
def masked_by_timing(netlist: Netlist, pulse: Pulse, timing_info: TimingInfo) -> bool:
    # boundaries specified by setup/hold time
    first_safe_time = timing_info.hold_time_ps
    last_safe_time = timing_info.clock_period_ps - timing_info.setup_time_ps

    # total propagation delay to output register from the affected net\
    if pulse.net not in netlist.wires:
        print(f"Warning: {pulse.net} not in netlist")
        return False
    output_delay_ns = netlist.wires[pulse.net].output_delay
    output_delay_ps = np.round(output_delay_ns * 1000)

    # range of times the bitflip is seen at the output register
    first_time_to_reg = (pulse.start_time_ps + output_delay_ps) % timing_info.clock_period_ps
    last_time_to_reg = (pulse.end_time_ps + output_delay_ps) % timing_info.clock_period_ps

    return first_time_to_reg > first_safe_time and last_time_to_reg < last_safe_time

# determines whether a pulse violates the setup or hold time on any clock cycle.
# this determines whether or not a pulse may cause a metastable output
def violates_setup_hold(netlist: Netlist, pulse: Pulse, timing_info: TimingInfo) -> bool:
    # boundaries specified by setup/hold time
    first_safe_time = timing_info.hold_time_ps
    last_safe_time = timing_info.clock_period_ps - timing_info.setup_time_ps

    # total propagation delay to output register from the affected net
    output_delay_ns = netlist.wires[pulse.net].output_delay
    output_delay_ps = np.round(output_delay_ns * 1000)

    # range of times the bitflip is seen at the output register
    first_time_to_reg = (pulse.start_time_ps + output_delay_ps) % timing_info.clock_period_ps
    last_time_to_reg = (pulse.end_time_ps + output_delay_ps) % timing_info.clock_period_ps

    return first_time_to_reg < first_safe_time or \
           first_time_to_reg > last_safe_time or \
           last_time_to_reg < first_safe_time or \
           last_time_to_reg > last_safe_time


def analyze_faults(netlist: Netlist, num_faults: int, timing_info: TimingInfo) -> float:
    # don't want to sample output wires
    filtered_wire_list = [v.name for (k, v) in netlist.wires.items() if not v.is_output]
    wire_name_to_index = {
        v.name: i for i, (k, v) in enumerate(netlist.wires.items())
    }

    sampled_net_list = []
    for _ in range(0, num_faults):
        net_name, net_idx = sample_net(filtered_wire_list)
        sampled_net_list.append(net_name)


    num_timing_masked_faults = 0
    num_metastable_faults = 0
    fault_nets = []

    for net_name in sampled_net_list:
        net: GraphWire = netlist.wires[net_name]
        start_time_ps = sample_cycle_time(timing_info.clock_period_ns)
        width_ps = sample_pulse_width()
        end_time_ps = start_time_ps + width_ps

        pulse = Pulse(net_name, start_time_ps, end_time_ps)
        is_masked = False
        is_metastable = False
        if masked_by_timing(netlist, pulse, timing_info):
            num_timing_masked_faults += 1
            is_masked = True
        elif violates_setup_hold(netlist, pulse, timing_info):
            num_metastable_faults += 1
            is_metastable = True
        fault_nets.append((net_name, is_masked, is_metastable))

    # write visible indices to file
    INDEX_FILENAME= f"{os.getcwd()}/generated/testbench/{netlist.name}_net_indices_hex.gen"
    with (open(INDEX_FILENAME, "w")) as f:
        for (net_name, is_timing_masked, is_metastable) in fault_nets:
            # convert to index in the filtered wire list
            net_idx = wire_name_to_index[net_name]
            f.write(f"{net_idx:04x} {is_timing_masked:01b} {is_metastable:01b}\n")

    # generate a testbench
    num_logic_masked_faults = 0
    if len(fault_nets) != 0:
        gen_testbench(netlist, len(fault_nets))

        # run simulation
        vcs_cmd = f"{VCS} {VCS_FLAGS} {VCS_SRC} {netlist.filepath} -o {SIM_EXE_NAME}"
        os.makedirs("build", exist_ok=True)
        subprocess.run(vcs_cmd, shell=True)
        subprocess.run(f"./{SIM_EXE_NAME}")

        # calculate masking ratio
        with open("generated/testbench/tb_output.txt", "r") as f:
            num_logic_masked_faults = int(f.read().strip())

    fault_mask_ratio = num_logic_masked_faults / num_faults

    print("TIMING MASKED: ", num_timing_masked_faults)
    print("METASTABLE: ", num_metastable_faults)
    print("LOGIC MASKED: ", num_logic_masked_faults)

    return fault_mask_ratio

def test_main():
    print("Running analyze_faults as script")
    netlists = parse_netlist("modules/full_adder_64bit.vg")
    print("Parsed netlist")
    for module_name, netlist in netlists:
        #print(netlist.wires)
        print(f"FMR: {analyze_faults(netlist, 1000000, TimingInfo(5, 0.1, 0.1))}\n")

if __name__ == '__main__':
    test_main()
