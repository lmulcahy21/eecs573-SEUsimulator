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
    def __init__(self, name: str, driver = None, loads = [], is_input = False, is_output = False):
        self.name = name              # Wire name (e.g., "n3", "carry_out")
        self.driver: Optional[GraphGate] = driver  # Gate that drives this wire (None if primary input)
        self.loads: List[GraphGate] = loads   # Gates that use this wire as an input
        self.is_input: bool = is_input   # True if primary input
        self.is_output: bool = is_output  # True if primary output

    def __repr__(self):
        return f"Wire({self.name}, driver={self.driver.name if self.driver else None}, loads={[g.name for g in self.loads]})"

class GraphGate:
    """Represents a gate instance in the netlist."""
    def __init__(self, name: str, gate_type: str, delay: Optional[float] = None):
        self.name = name            # Instance name (e.g., "U3")
        self.gate_type = gate_type  # Gate type (e.g., "xor2s2")
        self.delay = delay          # Propagation delay (if specified)
        self.inputs: List[Wire] = [] # Input wires
        self.output: Optional[Wire] = None  # Output wire

    def __repr__(self):
        return f"Gate({self.name}, type={self.gate_type}, inputs={[w.name for w in self.inputs]}, output={self.output.name if self.output else None})"



class Netlist:
    """Maintains the graph of wires and gates parsed from the AST."""
    def __init__(self):
        self.wires: Dict[str, GraphWire] = {}  # name -> Wire
        self.gates: Dict[str, GraphGate] = {}  # name -> Gate

    def add_wire(self, wire: GraphWire) -> None:
        if wire.name not in self.wires:
            self.wires[wire.name] = wire

    def parse_ast(self, ast):
        # Track primary inputs/outputs first
        print("Parsing module:", ast.name)
        for node in ast.children():
            match node:
                case Paramlist():
                    # parameters ignored? not part of structural verilog i dont think
                    print("Ignoring parameters")
                    continue
                case Portlist():
                    # process ports, effectively ignore
                    print("Ignoring ports")
                    # input/output ports
                    continue
                case Decl():
                    # process declarations
                    print("Processing declarations")
                    # process declaration, can be input, output, wire
                    for decl in node.children():
                        self._parse_decl(decl)
                case _:
                    # ignore gate instantiation on first pass, ensure have full wire mapping
                    continue
        for child in ast.children():
            # process instances
            match child:
                case InstanceList():
                    # process instances
                    for inst in child.children():
                        # process each instance
                        print("Processing instance:", inst.name)
                        gate_type = inst.module
                        self._parse_gate_instance(gate_type, inst)
                case _:
                    # other types of nodes
                    continue



    def _parse_gate_instance(self, gate_type: str, inst):
        gate = GraphGate(inst.name, gate_type)
        self.add_gate(gate)

        # Connect input/output wires
        for port in inst.portlist:
            if not isinstance(port, PortArg):
                continue
            wire = self.add_wire(port.argname.name)

            if port.portname == 'Q':  # Output port (assuming 'Q' is output)
                gate.output = wire
                wire.driver = gate
            else:                     # Input port
                gate.inputs.append(wire)
                wire.loads.append(gate)

        # Handle delay (e.g., `xor2s2 #5 U1(...)`)
        if hasattr(inst, 'delay') and inst.delay:
            gate.delay = float(inst.delay.value)
    def _parse_decl(self, decl):
        width_val = 1
        is_input = False
        is_output = False
        match decl:
            case Input():
                # input declaration
                print("Input declaration")
                # create a wire for each input
                is_input = True
            case Output():
                is_output = True
            case Wire():
                pass

        if decl.width is not None:
            width: Width = decl.width
            width_val = int(width.msb.value) - int(width.lsb.value) + 1
        for i in range(width_val):
            # create a wire for the graph
            name = decl.name if width == 1 else f"{decl.name}_{i}"
            wire = GraphWire(f"{decl.name}_{i}", is_input=is_input, is_output=is_output)
            self.add_wire(wire)


class tempvisitor(NodeVisitor):
    def visit(self, node):
        print(f"Visiting node: {node.__class__.__name__}")
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)
    def visit_ModuleDef(self, node):
        print(f"Visiting ModuleDef: {node.name}")
        netlist = Netlist()
        netlist.parse_ast(node)
        return netlist

def main():
    ast, directives = parse(['full_adder_64bit.vg'])
    instances = []
    visitor = tempvisitor()
    visitor.visit(ast)


if __name__ == "__main__":
    main()