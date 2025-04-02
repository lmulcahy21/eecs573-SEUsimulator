import argparse

class Netlist:
    None

def parse_netlist(netlist_filename: str) -> Netlist:
    # parse the netlist file and store the information in output struct
    # make chat write this lol
    return


# command line options for providing input and whatever
def main():
    parser = argparse.ArgumentParser(description="Nathan")
    parser.add_argument('--input', metavar='FILE', required=True,
                        help='Specify the input netlist')
    parser.add_argument('--period', metavar='PERIOD', )
    args = parser.parse_args()

    netlist_filename = args.input
    netlist = parse_netlist(netlist_filename)

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