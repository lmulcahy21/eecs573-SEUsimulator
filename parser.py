import argparse
from pyverilog.vparser.parser import parse
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

# Parse Verilog file
import pyverilog.vparser.ast as ast
from pyverilog.vparser.ast import *
from pyverilog.dataflow.visit import NodeVisitor

from typing import List, Dict, Optional

# ast:
#  Description
#       - ModuleDef
#           - ParamList
#           - PortList

# Module:        self.lineno = lineno
        # self.name = name
        # self.paramlist = paramlist
        # self.portlist = portlist
        # self.items = items
        # self.default_nettype = default_nettype

# Goal: break up the parsed AST into a graph of connections, each wire has ptr to where

# Graph represented by adjacency list
# Nodes are both inputs and intermediate wires

class GraphWire:
    """Represents a wire in the netlist, with connections to driving/driven gates."""
    def __init__(self, name: str, is_input = False, is_output = False):
        self.name = name              # Wire name (e.g., "n3", "carry_out")
        self.driver: Optional[GraphGate] = None # Gate that drives this wire (None if primary input)
        self.loads: List[GraphGate] = []  # Gates that load this wire (None if primary output)
        self.is_input: bool = is_input   # True if primary input
        self.is_output: bool = is_output  # True if primary output

    def __repr__(self):
        return f"Wire({self.name}, driver={self.driver.name if self.driver else None}, loads={[g.name for g in self.loads]}, is_input={self.is_input}, is_output={self.is_output})"
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


    def __init__(self, gate_instance: Instance, delay: Optional[float] = None):
        self.name: str = gate_instance.name            # Instance name (e.g., "U3")
        self.gate_type: str = gate_instance.module  # Gate type (e.g., "xor2s2")
        self.delay: int = delay          # Propagation delay (if specified)
        # process the portlist to get input/output wires
        visitor = self.GateVisitor()
        visitor.visit(gate_instance)

        self.inputs: List[str] = visitor.inputs # Input wires
        self.output: Optional[str] = visitor.output  # Output wire

    def __repr__(self):
        return f"Gate({self.name}, type={self.gate_type}, inputs={[w for w in self.inputs]}, output={self.output if self.output else None})"



class Netlist:
    """Maintains the graph of wires and gates parsed from the AST."""
    def __init__(self):
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
        # Track primary inputs/outputs first
        for node in ast.children():
            match node:
                case Paramlist():
                    continue
                case Portlist():
                    # input/output ports, syntactic sugar and declared in the module, structural verilog
                    continue
                case Decl():
                    # process declaration, can be input, output, wire
                    for decl in node.children():
                        self._parse_decl(decl)
                case _:
                    # ignore gate instantiation on first pass, ensure have full wire mapping
                    continue
        # Now process gate instances
        for node in ast.children():
            # process instances
            match node:
                case InstanceList():
                    # process instances
                    for inst in node.children():
                        # process each instance
                        self._parse_gate_instance(inst)
                case _:
                    # other types of nodes
                    continue

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


        # create a wire for each bit in the declaration
        for i in range(width_val):
            # create a wire for the graph
            name = decl.name if width_val == 1 else f"{decl.name}_{i}"
            wire = GraphWire(name, is_input=is_input, is_output=is_output)
            self.add_wire(wire)

    def _parse_gate_instance(self, gate_inst: Instance) -> GraphGate:
        """Parse an instance of a gate and create a corresponding GraphGate."""
        # create a gate instance
        gate = GraphGate(gate_inst)
        self.add_gate(gate)
        # connect the gate to the input wires that drives it
        for input_name in gate.inputs:
            if input_name not in self.wires.keys():
                print(f"Warning: Input wire {input_name} not found for gate {gate.name}")
                continue
            wire = self.wires[input_name]
            wire.add_load(gate)

        # connect the gate to the output wire it drives
        if gate.output:
            if gate.output not in self.wires.keys():
                print(f"Warning: Output wire {gate.output} not found for gate {gate.name}")
                return gate
            # connect the gate to the wire
            wire = self.wires[gate.output]
            wire.add_driver(gate)
        else:
            print(f"Warning: Gate {gate.name} has no output wire")
        return gate



class NetListVisitor(NodeVisitor):
    """Visitor class to traverse AST and construct the netlist per module"""
    def __init__(self):
        super().__init__()
        self.module_netlists: Dict[str, Netlist] = {}  # module name -> Netlist
    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def visit_ModuleDef(self, node):
        node: ModuleDef = node
        netlist = Netlist()
        netlist.parse_module(node)
        self.module_netlists[node.name] = netlist
        return

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
        print(f"Module: {module_name}")
        print("Wires:")
        for wire in netlist.wires.values():
            print(wire)
        print("Gates:")
        for gate in netlist.gates.values():
            print(gate)



if __name__ == "__main__":
    main()

