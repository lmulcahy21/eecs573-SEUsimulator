import argparse
from pyverilog.vparser.parser import parse
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

# Parse Verilog file
import pyverilog.vparser.ast as ast
from pyverilog.vparser.ast import *
from pyverilog.dataflow.visit import NodeVisitor

from typing import List, Dict, Optional, Tuple
from queue import LifoQueue

class GraphWire:
    """Represents a wire in the netlist, with connections to driving/driven gates."""
    def __init__(self, name: str, is_input = False, is_output = False):
        self.name = name              # Wire name (e.g., "n3", "carry_out")
        self.driver: Optional[GraphGate] = None # Gate that drives this wire (None if primary input)
        self.loads: List[GraphGate] = []  # Gates that load this wire (None if primary output)
        self.is_input: bool = is_input   # True if primary input
        self.is_output: bool = is_output  # True if primary output
        self.width = 0
        self.output_distance: int = 0  # Distance to the output wire (for delay calculation)
        self.output_delay: int = 0     # Delay to the output wire (for delay calculation)

    def __repr__(self):
        return f"Wire({self.name}, driver={self.driver.name if self.driver else None}, loads={[g.name for g in self.loads]}, is_input={self.is_input}, is_output={self.is_output}, distance={self.output_distance}, width={self.width})"

    def add_driver(self, gate) -> None:
        """Add a gate as a driver for this wire."""
        if self.driver is None:
            self.driver = gate
        else:
            print(f"Warning: Wire {self.name} already has a driver {self.driver.name}, skipping addition.")
            return

    def add_load(self, gate) -> None:
        """Add a gate as a load for this wire."""
        if gate not in self.loads:
            self.loads.append(gate)
        else:
            # TODO: This can happen if the same gate has this wire as an input multiple times, so check to avoid displaying this
            # ex:   oai322s1 U670 ( .DIN1(n380), .DIN2(n382), .DIN3(n381), .DIN4(n382),
            #                       .DIN5(n379), .DIN6(n318), .DIN7(n317), .Q(n384) ); from 64 bit adder
            print(f"Warning: Wire {self.name} already has load {gate.name}, skipping duplicate addition ({[g.name for g in self.loads]}).")
            return

class GraphGate:
    """Represents a gate instance in the netlist."""
    class GateVisitor(NodeVisitor):
        def __init__(self):
            super().__init__()
            self.inputs: List[str] = []  # List of input wire names
            self.output: Optional[str] = None  # Output wire name

        def process_argname(self, argname):
            if isinstance(argname, ast.Identifier):
                # argname is a wire name
                return argname.name
            elif isinstance(argname, ast.Pointer):
                # argname is a pointer to a wire
                # process the pointer to get the wire name
                return f"{argname.var}_{argname.ptr}"
            else:
                # unknown type
                print(f"Unknown argname type: {argname.__class__.__name__}")
                return None

        def visit_PortArg(self, node: PortArg):
            # set self values
            if node.portname == "Q":
                # output port
                if self.output is not None:
                    print(f"Warning: Multiple output ports found on line {node.lineno}")
                    return
                self.output = self.process_argname(node.argname)
            else:
                # input port
                self.inputs.append(self.process_argname(node.argname))
            return (self.inputs, self.output)


    def __init__(self, gate_instance: Instance, wires: Dict[str, GraphWire], delay: Optional[float] = 1):
        self.name: str = gate_instance.name            # Instance name (e.g., "U3")
        self.gate_type: str = gate_instance.module  # Gate type (e.g., "xor2s2")
        self.delay: int = delay          # Propagation delay (default 1)
        self.inputs: List[GraphWire] = []      # Input wires
        self.output: Optional[GraphWire] = None # Output wire

        self.output_distance: int = 0  # Distance to the output wire (for delay calculation)
        self.output_delay: int = 0     # Delay to the output wire (for delay calculation)

        # process the portlist to get input/output wires
        visitor = self.GateVisitor()
        visitor.visit(gate_instance)
        self.inputs = [wires[s] for s in visitor.inputs]
        self.output = wires[visitor.output] if visitor.output else None

    def __repr__(self):
        return f"""Gate({self.name}, type={self.gate_type}, inputs={[w.name for w in self.inputs]}, output={self.output.name if self.output else None})"""



class Netlist:
    """Maintains the graph of wires and gates parsed from the AST."""
    def __init__(self):
        self.name: str
        self.filepath: str
        self.inputs: List[Tuple[str, int]] = [] # signal name, width
        self.outputs: List[Tuple[str, int]] = [] # signal name, width
        self.wires: Dict[str, GraphWire] = {}  # name -> Wire
        self.gates: Dict[str, GraphGate] = {}  # name -> Gate


    def add_wire(self, wire: GraphWire) -> None:
        if wire.name not in self.wires:
            self.wires[wire.name] = wire
        else:
            print(f"Warning: Wire {wire.name} already exists, skipping addition.")
            return

    def add_gate(self, gate: GraphGate) -> None:
        if gate.name not in self.gates:
            self.gates[gate.name] = gate
        else:
            print(f"Warning: Gate {gate.name} already exists, skipping addition.")
            return

    def parse_module(self, ast):
        # Declarations of all necessary wires between gates
        # and the gates themselves will be before they are used
        # in module instantiations, so can process in one pass
        self.name = ast.name
        output_wires: List[GraphWire] = []
        for node in ast.children():
            match node:
                case Decl():
                    for decl in node.children():
                        self._parse_decl(decl)
                case InstanceList():
                    # process instances
                    for inst in node.children():
                        # process each instance
                        self._parse_gate_instance(gate_inst=inst)
                case _:
                    # ports/parameters ignored, because structural verilog ignores those
                    continue


        # now we have all the wires and gates, we can calculate the delays by calculating the distances from outputs
        # traverse the graph from output wires to input wires, storing the maximum gate distance to an output wire


        output_wires = list(filter(lambda v: v.is_output, [v for (k,v) in self.wires.items()]))
        self.calculate_delays(output_wires)
        # output wire (0) -> driving gate -> input wires (1) -> driving gates -> input wires (2) -> driving gate (3)
        return

    def calculate_delays(self, output_wires: List[GraphWire]) -> None:
        """Calculate the delays from output wires to input wires."""
        # use a stack to traverse the graph
        # print(output_wires)
        stack = LifoQueue()
        for wire in output_wires:
            stack.put((wire, None))  # push the output wire and None as the previous gate

        # max output delay to a wire/gate is the max of the current and the gate we came from's delay (plus one if we're a gate)
        while not stack.empty():
            # stack tuple holds a pair of (wire, gate that takes wire as input) so (wire, load_gate)
            t: Tuple[GraphWire, GraphGate] = stack.get()
            wire, load_gate = t
            if load_gate is not None:
                # if the load gate is not None, intermed or input wire
                wire.output_distance = max(wire.output_distance, load_gate.output_distance + 1)
                wire.output_delay = max(wire.output_delay, load_gate.output_delay) # don't add, because gates come with own delay
            driving_gate = None
            if wire.driver:
                # process driving gate, should only ever happen once per gate BUT JUST IN CASE
                driving_gate = wire.driver
                driving_gate.output_distance = max(wire.output_distance, driving_gate.output_distance)
                # delay is max of wire output delay + self delay, max is just for sanity, should only get set once
                driving_gate.output_delay = max(wire.output_delay + driving_gate.delay, driving_gate.output_delay)

            if driving_gate:
                # add this gate with all its loads to the stack
                for input_wire in driving_gate.inputs:
                    stack.put((input_wire, driving_gate))


    def _parse_decl(self, decl):
        """Parse a declaration (input, output, wire) and create corresponding GraphWire."""
        width_val = 1
        is_input = False
        is_output = False
        match decl:
            case Input():
                is_input = True
            case Output():
                is_output = True
            case Wire():
                pass
            case _:
                print(f"Unknown declaration type: {decl.__class__.__name__}")

        if decl.width is not None:
            width: Width = decl.width
            width_val = int(width.msb.value) - int(width.lsb.value) + 1

        if is_input:
            # add (name, width)
            self.inputs.append((decl.name, width_val))
        if is_output:
            self.outputs.append((decl.name, width_val))
        # create a wire for each bit in the declaration
        for i in range(width_val):
            # create a wire for the graph
            name = decl.name if width_val == 1 else f"{decl.name}_{i}"
            wire = GraphWire(name, is_input=is_input, is_output=is_output)
            wire.width = width_val
            self.add_wire(wire)

    def _parse_gate_instance(self, gate_inst: Instance) -> GraphGate:
        """Parse an instance of a gate and create a corresponding GraphGate."""
        # create a gate instance
        gate = GraphGate(gate_inst, self.wires)
        # gate has references to all wires it connects to, both loads and drive
        self.add_gate(gate)
        # connect the gate to the input wires that drives it
        for input_wire in gate.inputs:
            # store reference to the gate in the input wire
            input_wire.add_load(gate)
        # connect the gate to the output wire it drives
        if gate.output:
            # store reference to the gate in the output wire
            gate.output.add_driver(gate)
        else:
            print(f"Warning: Gate {gate.name} has no output wire")
        return gate



class NetListVisitor(NodeVisitor):
    """Visitor class to traverse AST and construct the netlist per module"""
    def __init__(self, netlist_filename: str):
        super().__init__()
        self.module_netlists: Dict[str, Netlist] = {}  # module name -> Netlist
        self.netlist_filename = netlist_filename

    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def visit_ModuleDef(self, node):
        node: ModuleDef = node
        netlist = Netlist()
        netlist.filepath = self.netlist_filename
        netlist.parse_module(node)
        self.module_netlists[node.name] = netlist
        return

def parse_netlist(netlist_filename: str):
    ast, directives = parse(filelist=[netlist_filename], outputdir="./generated/parser")
    visitor = NetListVisitor(netlist_filename)
    visitor.visit(ast)
    return visitor.module_netlists.items()

def main():
    parser = argparse.ArgumentParser(description="Nathan")
    parser.add_argument('input_file', metavar='FILE', help='Specify the input netlist') # positional arg
    parser.add_argument('--period', metavar='PERIOD', required=False, help='Specify the clock period')
    args = parser.parse_args()

    netlist_filename = args.input_file

    ast, directives = parse([netlist_filename])
    instances = []
    visitor = NetListVisitor()
    visitor.visit(ast)
    for module_name, netlist in visitor.module_netlists.items():
        print(f"Module: {netlist.name}")
        print("Inputs:")
        for input in netlist.inputs:
            print(input)
        print("Outputs:")
        for output in netlist.outputs:
            print(output)
        print("Wires:")
        for wire in netlist.wires.values():
            print(wire)
        print("Gates:")
        for gate in netlist.gates.values():
            print(gate)
        print(f"Num wires: {len(netlist.wires)}")



if __name__ == "__main__":
    main()

