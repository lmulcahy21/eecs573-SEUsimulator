from parser import Netlist
from gen_testbench import gen_testbench
import random
import numpy as np
from scipy.stats import poisson

LAM = 50

def sample_net(netlist: Netlist) -> str:
    return random.choice(netlist.wires_list)

def sample_cycle_time(period_ns: int, lam: int) -> int:
    period_ps = 1000 * period_ns
    k_values = np.arange(1, period_ps + 1)
    pmf = poisson.pmf(k_values, lam)

    pmf_normalized = pmf / pmf.sum()

    sample = np.random.choice(k_values, p=pmf_normalized)
    return sample

def sample_pulse_width() -> int:
    # exponential or log-normal distribution?
    # short much more common than long
    return 2

def analyze_faults(netlist: Netlist, num_faults: int, clock_period_ns: int, setup_time_ns: int, hold_time_ns: int):
    # sample nets, start times, and widths for each fault
    visible_fault_nets = []
    masked_faults_timing = 0
    metastable_faults = 0

    for _ in range(0, num_faults):
        start_time_ps = sample_cycle_time(clock_period_ns, LAM)
        width_ps = sample_pulse_width()
        end_time_ps = start_time_ps + width_ps
        
        clock_period_ps = clock_period_ns * 1000
        setup_time_ps = setup_time_ns * 1000
        hold_time_ps = hold_time_ns * 1000
        setup_threshold_ps = clock_period_ps - setup_time_ps
        hold_threshold_ps = hold_time_ps
        # statically analyze timing information
        # determine which faults will never be seen
        if start_time_ps > hold_threshold_ps and end_time_ps < setup_threshold_ps:
            masked_faults_timing += 1

        # determine which faults will cause metastability
        elif start_time_ps < hold_threshold_ps or start_time_ps > setup_threshold_ps or \
            end_time_ps < hold_threshold_ps or end_time_ps > setup_threshold_ps:
            metastable_faults += 1

        # simulate all other faults by generating testbench
        else:
            net = sample_net(netlist)
            visible_fault_nets.append(net)
        
    # generate a testbench
    gen_testbench(visible_fault_nets)

    # run simulation
    # call os function with vcs or something

    # report results  

    return

def main():
    analyze_faults()

if __name__ == '__main__':
    main()