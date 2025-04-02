from pyverilog.vparser.parser import parse
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

# Parse Verilog file
ast, directives = parse(['full_adder_1bit.vg'])
ast.show()
# Traverse AST to extract instances and connections
from pyverilog.vparser.ast import InstanceList, PortArg




def main():
    instances = []
    for child in ast.children():
        if isinstance(child, InstanceList):
            for inst in child.instances:
                instance_name = inst.name
                module_type = child.module
                print(module_type)
                ports = []
                for port in inst.portlist:
                    if isinstance(port, PortArg):
                        ports.append((port.portname, port.argname))
                instances.append({
                    'type': module_type,
                    'name': instance_name,
                    'ports': ports
                })


if __name__ == "__main__":
    main()