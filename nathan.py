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
# generate systemverilog file with augmented interface for injecting faults
# -- insert xor after every single gate
# -- when we parse netlist make note of output wire name OW
# -- insert xor with input OW and new input (for control), call output of XOR OX
# -- any gate that took OW as input now takes OX as input instead
# -- note: this affects timing. Should we add a special xor gate with zero delay?
# -- nevermind haha just touch the wires
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