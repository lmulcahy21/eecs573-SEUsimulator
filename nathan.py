import argparse
from nathan_parser import Netlist, parse_netlist
import os
import numpy as np
from analyze_faults import analyze_faults
from nathan_types import TimingInfo

DESCRIPTION_STR = \
"""
NATHAN is a tool for evaluating combinational logic modules (adders, \
multipliers, etc.) when subjected to single-event upsets (bit-flips) caused \
by, e.g., pulses of ionizing radiation.

NATHAN generates statistics about the effects of transient faults on module \
outputs and the rates of masking due to timing and the structure of the module \
itself.
"""

def validate_args(args) -> bool:
    # validate module netlist file exists
    if not os.path.exists(args.module):
        print("Invalid argument to --module: file not found")
        return False

    # validate number of faults
    try:
        int(args.num_faults)
    except:
        print("Invalid argument to --num_faults: must be a positive integer")
        return False

    if int(args.num_faults) <= 0:
        print("Invalid argument to --num_faults: must be a positive integer")
        return False

    return True

def main():
    parser = argparse.ArgumentParser(prog="NATHAN", description=DESCRIPTION_STR)
    parser.add_argument('-m', '--module', metavar='FILE', required=True,
                        help='Specify the input netlist')
    parser.add_argument('-n', '--num_faults', metavar='NUM', required=True,
                        help='Specify the number of faults to inject')
    parser.add_argument('-l', '--gate_library', metavar='LIB', required=False,
                        help='Specify the gate library to use for parsing and simulation')
    parser.add_argument('-s', '--sdf', metavar='FILE', required=False,
                        help='Specify module timing information in Standard Data Format (SDF)')
    parser.add_argument('-p', '--period', metavar='PERIOD', required=True,
                        help='Specify the clock period in nanoseconds (ns)')
    parser.add_argument('-st', '--setup_time', metavar='TIME', required=True,
                        help='Specify the register setup time in nanoseconds (ns)')
    parser.add_argument('-ht', '--hold_time', metavar='TIME', required=True,
                        help='Specify the register hold time in nanoseconds (ns)')
    
    # parser.add_argument('-v', '--verbose', action='store_true', required=False,
    #                     help='Do not suppress additional output')
    # TRUERANDOM vs seed option - https://www.doulos.com/media/1293/snug2013_sv_random_stability_paper.pdf

    args = parser.parse_args()
    if not validate_args(args):
        parser.print_help()
        return

    netlists = parse_netlist(args.module)
    assert len(netlists) == 1 # TODO: remove this? not sure.
    for module_name, netlist in netlists:
        timing_info = TimingInfo(float(args.period), float(args.setup_time), float(args.hold_time))
        analyze_faults(netlist, timing_info, int(args.num_faults), args.sdf)

if __name__ == '__main__':
    main()