import argparse
from analyze_faults import analyze_faults
from nathan_parser import Netlist, parse_netlist
import os

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
    parser = argparse.ArgumentParser(description="Nathan")
    parser.add_argument('--module', metavar='FILE', required=True,
                        help='Specify the input netlist')
    # parser.add_argument('--period', metavar='PERIOD', )
    # parser.add_argument('--period-unit', metavar='UNIT')
    parser.add_argument('--num_faults', metavar='NUM', required=True,
                        help='Specify the number of faults to inject')
    # parser.add_argument('--encoding-scheme', metavar='SCHEME', ) #e.g. AN, etc.
    # parser.add_argument('--setup-time')
    # parser.add_argument('--hold-time')
    # parser.add_argument('--clock-period')
    # parser.add_argument('--clock-period-unit')
    args = parser.parse_args()

    if not validate_args(args):
        print("Invalid arguments")
        parser.print_help()
        return

    netlists = parse_netlist(args.module)
    module_path = args.module
    assert(len(netlists) == 1) # TODO: remove this? not sure.
    for module_name, netlist in netlists:
        fmr = analyze_faults(netlist, int(args.num_faults), args)
    print(f"\nFMR: {fmr}\n")

# input: netlist

# run NATHAN
# steps:

# Parse structural verilog file, combinational logic only
# -- Chat:
# 1. Read the structural Verilog and extract all gates, their types, input/output ports, and connected wires.
# 2. For each wire, determine its driver (the gate's output that drives it) and the loads (the gate inputs connected to it).
# 3. For each gate, record its delay (either from the Verilog or a default based on type).
# 4. Build a directed graph where nodes are gates and edges represent the connectivity via wires, annotated with delays.
# 5. For each wire, compute the maximum propagation delay from that wire to each output. This can be done using a topological sort and dynamic programming, propagating delays from outputs back to inputs or vice versa.

# Generate testbench code to inject faults
# -- for each input wire, random input, calculate "correct" output
# -- inject faults based on user's poisson distribution (fault rate is poisson) on random uniform gate
# -- check if it catches the error w/ AN code, or if it gets masked
# -- any way to do metastability? if within setup/hold time? verilog timing stuff

# AN encoder and decoder
# generate testbench
# run simulation
# -- when we do all of the sampling relevant for a SEU, first precompute information
#    about the timing -- this makes it so that we know whether masking/metastability
#    is going to occur ahead of time -- so we don't care about timing perhaps when
#    simulating the design

# cleanup - delete netlist?

# TODOs at the moment:
# we are going to build a big ass graph
# nodes are gates, edges are wires, node value is gate delay, edge weight is
#      potential wire delay (take as input?)
#  ?????
# profit


if __name__ == '__main__':
    main()